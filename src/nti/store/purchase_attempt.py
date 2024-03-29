#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import copy
import time
from functools import total_ordering

import BTrees

from persistent.mapping import PersistentMapping

import six

from zope import component
from zope import interface

from zope.annotation.interfaces import IAttributeAnnotatable

from zope.container.contained import Contained

from zope.mimetype.interfaces import IContentTypeAware

from zope.schema.fieldproperty import FieldPropertyStoredThroughField as FP

from nti.base._compat import text_

from nti.base.interfaces import ICreated

from nti.dataserver.interfaces import IUser

from nti.dataserver.users.interfaces import IUserProfile

from nti.dataserver.users.user_profile import get_searchable_realname_parts

from nti.dublincore.time_mixins import ModifiedTimeMixin as ModDateTrackingObject

from nti.externalization.interfaces import IInternalObjectExternalizer

from nti.externalization.representation import WithRepr

from nti.mimetype.mimetype import MIME_BASE

from nti.ntiids.ntiids import find_object_with_ntiid

from nti.ntiids.oids import to_external_ntiid_oid

from nti.property.property import alias

from nti.schema.eqhash import EqHash

from nti.schema.fieldproperty import createDirectFieldProperties

from nti.schema.schema import SchemaConfigured

from nti.store.interfaces import PA_STATE_FAILED
from nti.store.interfaces import PA_STATE_FAILURE
from nti.store.interfaces import PA_STATE_SUCCESS
from nti.store.interfaces import PA_STATE_UNKNOWN
from nti.store.interfaces import PA_STATE_STARTED
from nti.store.interfaces import PA_STATE_PENDING
from nti.store.interfaces import PA_STATE_DISPUTED
from nti.store.interfaces import PA_STATE_CANCELED
from nti.store.interfaces import PA_STATE_REDEEMED
from nti.store.interfaces import PA_STATE_REFUNDED
from nti.store.interfaces import PA_STATE_RESERVED

from nti.store.interfaces import IPurchaseAttempt
from nti.store.interfaces import IGiftPurchaseAttempt
from nti.store.interfaces import IPurchaseAttemptContext
from nti.store.interfaces import IPurchaseAttemptFactory
from nti.store.interfaces import IRedeemedPurchaseAttempt
from nti.store.interfaces import IInvitationPurchaseAttempt

from nti.store.purchase_order import replace_quantity
from nti.store.purchase_order import get_providers as get_providers_from_order
from nti.store.purchase_order import get_currencies as get_currencies_from_order
from nti.store.purchase_order import get_purchasables as get_purchasables_from_order

from nti.store.utils import copy_object
from nti.store.utils import MetaStoreObject

from nti.traversal.traversal import find_interface

from nti.zodb import minmax

from nti.zodb.persistentproperty import PersistentPropertyHolder

logger = __import__('logging').getLogger(__name__)


@interface.implementer(IPurchaseAttemptContext, IInternalObjectExternalizer)
class DefaultPurchaseAttemptContext(PersistentMapping):
    """
    The default representation of context info.
    """

    def toExternalObject(self, *unused_args, **unused_kwargs):
        return dict(self)


def to_purchase_attempt_context(context):
    result = IPurchaseAttemptContext(context, None)
    return result


def empty_purchase_attempt_context():
    return DefaultPurchaseAttemptContext()


@six.add_metaclass(MetaStoreObject)
@WithRepr
@total_ordering
@EqHash("Order", "StartTime", "Processor")
@interface.implementer(ICreated,
                       IPurchaseAttempt,
                       IAttributeAnnotatable,
                       IContentTypeAware)
class PurchaseAttempt(ModDateTrackingObject,
                      SchemaConfigured,
                      Contained,
                      PersistentPropertyHolder):
    createDirectFieldProperties(IPurchaseAttempt)

    Context = FP(IPurchaseAttempt['Context'])
    
    __external_class_name__ = "PurchaseAttempt"

    id = alias('__name__')
    state = alias('State')
    context = alias('Context')
    createdTime = alias('StartTime')

    @property
    def Items(self):
        return self.Order.NTIIDs

    @property
    def Quantity(self):
        return self.Order.Quantity

    @property
    def creator(self):
        return find_interface(self, IUser, strict=False)
    Creator = creator

    @property
    def profile(self):
        return IUserProfile(self.creator)
    Profile = profile

    def __str__(self):
        return "%s,%s" % (self.Items, self.State)

    def __lt__(self, other):
        try:
            return self.StartTime < other.StartTime
        except AttributeError:
            return NotImplemented

    def __gt__(self, other):
        try:
            return self.StartTime > other.StartTime
        except AttributeError:
            return NotImplemented

    def has_failed(self):
        return self.State in (PA_STATE_FAILED, PA_STATE_FAILURE, PA_STATE_CANCELED)

    def has_succeeded(self):
        return self.State == PA_STATE_SUCCESS

    def is_unknown(self):
        return self.State == PA_STATE_UNKNOWN

    def is_pending(self):
        return self.State in (PA_STATE_STARTED, PA_STATE_PENDING)

    def is_refunded(self):
        return self.State == PA_STATE_REFUNDED

    def is_disputed(self):
        return self.State == PA_STATE_DISPUTED

    def is_reserved(self):
        return self.State == PA_STATE_RESERVED

    def is_canceled(self):
        return self.State == PA_STATE_CANCELED

    def has_completed(self):
        return not (self.is_pending() or self.is_reserved() or self.is_disputed())

    def is_synced(self):
        return self.Synced


@interface.implementer(IInvitationPurchaseAttempt)
class InvitationPurchaseAttempt(PurchaseAttempt):

    ExpirationTime = FP(IInvitationPurchaseAttempt['ExpirationTime'])

    def __init__(self, *args, **kwargs):
        super(InvitationPurchaseAttempt, self).__init__(*args, **kwargs)
        self._consumers = BTrees.OOBTree.OOBTree()
        self._tokens = minmax.NumericMinimum(self.Quantity)

    def reset(self):
        self._tokens.value = 0

    @property
    def consumerMap(self):
        return dict(self._consumers)

    def isExpired(self, now=None):
        now = now or time.time()
        result = bool(self.ExpirationTime and now > self.ExpirationTime)
        return result
    is_expired = isExpired

    def get_linked_purchase_id(self, user):
        user = getattr(user, "username", user)
        user = getattr(user, "id", user)
        return self._consumers.get(user.lower()) if user else None
    linked_purchase_id = get_linked_purchase_id

    def register(self, user, linked_purchase_id=None):
        user = getattr(user, "username", user)
        user = getattr(user, "id", user)
        if user and not user.lower() in self._consumers:
            self._consumers[user.lower()] = linked_purchase_id
            return True
        return False

    @property
    def tokens(self):
        return self._tokens.value

    def restore_token(self):
        if self._tokens.value < self.Quantity:
            self._tokens += 1
            return True
        return False

    def consume_token(self):
        if self._tokens.value > 0:
            self._tokens -= 1
            return True
        return False

    def __str__(self):
        return self.id


@interface.implementer(IRedeemedPurchaseAttempt)
class RedeemedPurchaseAttempt(PurchaseAttempt):

    RedemptionCode = FP(IRedeemedPurchaseAttempt['RedemptionCode'])
    RedemptionTime = FP(IRedeemedPurchaseAttempt['RedemptionTime'])
    SourcePurchaseID = FP(IRedeemedPurchaseAttempt['SourcePurchaseID'])

    @property
    def SourcePurchase(self):
        ntiid = self.SourcePurchaseID
        result = find_object_with_ntiid(ntiid) if ntiid else None
        return result


@interface.implementer(IUserProfile)
class GiftPurchaseUserProfile(object):

    backgroundURL = avatarURL = email = realname = alias = None  # User profile fields

    def get_searchable_realname_parts(self):
        return get_searchable_realname_parts(self.realname)


@interface.implementer(IGiftPurchaseAttempt)
class GiftPurchaseAttempt(PurchaseAttempt):

    Creator = FP(IGiftPurchaseAttempt['Creator'])
    Message = FP(IGiftPurchaseAttempt['Message'])
    Receiver = FP(IGiftPurchaseAttempt['Receiver'])
    SenderName = FP(IGiftPurchaseAttempt['SenderName'])
    ReceiverName = FP(IGiftPurchaseAttempt['ReceiverName'])
    DeliveryDate = FP(IGiftPurchaseAttempt['DeliveryDate'])
    TargetPurchaseID = FP(IGiftPurchaseAttempt['TargetPurchaseID'])

    receiver = alias('Receiver')
    to = To = alias('ReceiverName')
    creator = From = alias('Creator')
    sender = Sender = alias('SenderName')

    @property
    def profile(self):
        result = GiftPurchaseUserProfile()
        result.email = self.Creator
        result.alias = result.realname = self.Sender or self.Creator
        return result
    Profile = profile

    def has_succeeded(self):
        return self.State in (PA_STATE_SUCCESS, PA_STATE_REDEEMED)

    def is_redeemed(self):
        return self.State == PA_STATE_REDEEMED


def get_providers(purchase):
    return get_providers_from_order(purchase.Order)


def get_currencies(purchase):
    return get_currencies_from_order(purchase.Order)


def get_purchasables(purchase):
    return get_purchasables_from_order(purchase.Order)


def create_purchase_attempt(order, processor, state=None, description=None,
                            start_time=None, context=None, expiration=None):

    # set some defaults
    state = state or PA_STATE_UNKNOWN
    context = to_purchase_attempt_context(context)
    start_time = start_time if start_time else time.time()

    # if there is a quantity, it means it's an invitation purchase
    if order.Quantity:
        expiration = float(expiration) if expiration else None
        result = InvitationPurchaseAttempt(Order=order,
                                           Processor=processor,
                                           Description=description,
                                           State=state,
                                           Context=context,
                                           StartTime=float(start_time),
                                           ExpirationTime=expiration)
    else:
        # try to find a factory based on the providers of the
        # purchasables in the order
        factory = None
        providers = get_providers_from_order(order)
        if providers and len(providers) == 1:
            provider = providers[0].lower()
            factory = component.queryUtility(IPurchaseAttemptFactory,
                                             name=provider)

        if factory is None:
            factory = component.getUtility(IPurchaseAttemptFactory)

        result = factory.create(order=order, processor=processor, state=state,
                                description=description, start_time=start_time,
                                context=context)
    return result


def create_redeemed_purchase_attempt(purchase, redemption_code, items=(),
                                     redemption_time=None):

    items = items or purchase.Items
    redemption_time = redemption_time if redemption_time else time.time()

    # copy with order quantity none and item quantity to 1
    new_order = copy_object(purchase.Order, items=items)
    new_order.Quantity = None
    replace_quantity(new_order, 1)

    # copy context
    context = purchase.Context
    if context:
        context = copy.copy(context)
    else:
        context = empty_purchase_attempt_context()

    result = RedeemedPurchaseAttempt(Order=new_order,
                                     Processor=purchase.Processor,
                                     Description=purchase.Description,
                                     State=purchase.State,
                                     StartTime=purchase.StartTime,
                                     EndTime=purchase.EndTime,
                                     Error=purchase.Error,
                                     Synced=purchase.Synced,
                                     Context=context,
                                     RedemptionTime=float(redemption_time),
                                     RedemptionCode=text_(redemption_code),
                                     SourcePurchaseID=to_external_ntiid_oid(purchase))
    return result


def create_gift_purchase_attempt(creator, order, processor, state=None, description=None,
                                 start_time=None, sender=None, receiver=None,
                                 receiver_name=None, message=None, target=None,
                                 delivery_date=None, context=None):

    state = state or PA_STATE_UNKNOWN
    context = to_purchase_attempt_context(context)
    start_time = start_time if start_time else time.time()

    sender = sender or creator
    receiver_name = receiver_name or receiver
    context = context if context is not None else empty_purchase_attempt_context()
    result = GiftPurchaseAttempt(Order=order,
                                 Processor=processor,
                                 Creator=creator.lower(),
                                 Description=description,
                                 State=state,
                                 StartTime=float(start_time),
                                 Context=context,
                                 SenderName=sender,
                                 ReceiverName=receiver_name,
                                 Message=message,
                                 DeliveryDate=delivery_date,
                                 Receiver=receiver,
                                 TargetPurchaseID=target)
    return result


@interface.implementer(IPurchaseAttemptFactory)
class DefaultPurchaseAttemptFactory(object):

    # pylint: disable=keyword-arg-before-vararg
    def create(self, order, processor, state=None, description=None,
               start_time=None, context=None, *unused_args, **unused_kwargs):
        # set some defaults
        state = state or PA_STATE_UNKNOWN
        context = to_purchase_attempt_context(context)
        context = context if context is not None else empty_purchase_attempt_context()
        start_time = start_time if start_time else time.time()
        # create
        result = PurchaseAttempt(Order=order, Processor=processor,
                                 Description=description, State=state,
                                 StartTime=float(start_time), Context=context)
        return result


# deprecated


from nti.base.deprecation import hiding_warnings
with hiding_warnings():
    from nti.store.interfaces import IEnrollmentPurchaseAttempt

from zope.deprecation import deprecated

deprecated("EnrollmentPurchaseAttempt", "use proper course enrollment")
@interface.implementer(IEnrollmentPurchaseAttempt)
class EnrollmentPurchaseAttempt(PurchaseAttempt):
    mime_type = mimeType = MIME_BASE + 'enrollmentpurchaseattempt'
    Processor = FP(IEnrollmentPurchaseAttempt['Processor'])
