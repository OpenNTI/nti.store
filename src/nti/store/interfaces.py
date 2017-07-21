#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from zope.deprecation import deprecated

from zope.container.interfaces import IContained
from zope.container.interfaces import IContainer

from zope.interface.common.mapping import IEnumerableMapping

from zope.interface.common.sequence import IMinimalSequence

from zope.interface.interfaces import ObjectEvent
from zope.interface.interfaces import IObjectEvent

from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary

from nti.base.interfaces import IFile

from nti.contentfragments.schema import HTMLContentFragment

from nti.dataserver.interfaces import IUser

from nti.dataserver.users.interfaces import checkEmailAddress

from nti.invitations.interfaces import IInvitation
from nti.invitations.interfaces import IInvitationActor

from nti.namedfile.interfaces import IFileConstrained

from nti.schema.field import Int
from nti.schema.field import Bool
from nti.schema.field import Choice
from nti.schema.field import Number
from nti.schema.field import Object
from nti.schema.field import Variant
from nti.schema.field import Datetime
from nti.schema.field import TextLine
from nti.schema.field import ValidURI
from nti.schema.field import ValidText
from nti.schema.field import ListOrTuple
from nti.schema.field import ValidTextLine
from nti.schema.field import UniqueIterable

from nti.store.schema import DateTime

#: A :class:`zope.Interfaces.IVocabularyTokenized` vocabulary
#: will be available as a registered vocabulary under this name
PURCHASABLE_VOCAB_NAME = 'nti.store.purchasable.vocabulary'

PA_STATE_FAILED = u'Failed'
PA_STATE_SUCCESS = u'Success'
PA_STATE_FAILURE = u'Failure'
PA_STATE_PENDING = u'Pending'
PA_STATE_STARTED = u'Started'
PA_STATE_UNKNOWN = u'Unknown'
PA_STATE_DISPUTED = u'Disputed'
PA_STATE_REFUNDED = u'Refunded'
PA_STATE_CANCELED = u'Canceled'
PA_STATE_RESERVED = u'Reserved'
PA_STATE_REDEEMED = u'Redeemed'

PA_STATES = (PA_STATE_UNKNOWN, PA_STATE_FAILED, PA_STATE_FAILURE, PA_STATE_PENDING,
             PA_STATE_STARTED, PA_STATE_DISPUTED, PA_STATE_REFUNDED, PA_STATE_SUCCESS,
             PA_STATE_CANCELED, PA_STATE_RESERVED, PA_STATE_REDEEMED)
PA_STATE_VOCABULARY = \
    SimpleVocabulary([SimpleTerm(_x) for _x in PA_STATES])

PAYMENT_PROCESSORS = (u'stripe', u'payeezy')
PAYMENT_PROCESSORS_VOCABULARY = \
    SimpleVocabulary([SimpleTerm(_x) for _x in PAYMENT_PROCESSORS])


class IStore(interface.Interface):
    """
    Marker interface for a NTI Store
    """


class IItemBundle(interface.Interface):
    NTIID = ValidTextLine(title=u'Item bundle NTTID', required=True)

    Title = ValidTextLine(title=u'Item bundle title', required=False)

    Author = ValidTextLine(title=u'Item bundle author', required=False)

    Description = HTMLContentFragment(title=u'Content bundle description',
                                      required=False, 
                                      default=u'')

    Items = UniqueIterable(value_type=ValidTextLine(title=u'The item identifier'),
                           title=u"Bundle items")
    
    Label = ValidTextLine(title=u'Item bundle label', required=False)
    Label.setTaggedValue('_ext_excluded_out', True)
IContentBundle = IItemBundle  # BWC


class IPurchasableVendorInfo(IEnumerableMapping):
    """
    Arbitrary purchasable vendor-specific information

    This is simply a dictionary and this module does not define
    the structure of it. However, it is recommended that the top-level
    keys be the vendor names and within them be the actual vendor specific
    information.
    """


class IPurchasable(IItemBundle, IFileConstrained):

    Amount = Number(title=u"Cost amount", 
                    required=True, 
                    min=0.0)

    Currency = ValidTextLine(title=u'Currency amount',
                             required=True,
                             default=u'USD')

    Discountable = Bool(title=u"Discountable flag",
                        required=True, 
                        default=False)

    BulkPurchase = Bool(title=u"Bulk purchase flag",
                        required=True, 
                        default=False)

    Fee = Number(title=u"Percentage fee",
                 required=False, 
                 min=0.0)

    Icon = Variant((ValidTextLine(title=u"Icon source url"),
                    ValidURI(title=u"Icon source uri"),
                    Object(IFile, title=u"Icon file")),
                   title=u"Purchasable icon",
                   required=False)

    Thumbnail = ValidTextLine(title=u'Thumbnail URL', required=False)

    Provider = ValidTextLine(title=u'Purchasable item provider', required=True)

    License = ValidTextLine(title=u'Purchasable license', required=False)

    Public = Bool(title=u"Public flag", required=False, default=False)

    Giftable = Bool(title=u"Giftable flag", required=False, default=False)

    Redeemable = Bool(title=u"Redeemable flag", required=False, default=False)

    RedeemCutOffDate = DateTime(title=u"Redeem cutoff date", required=False)

    IsPurchasable = Bool(title=u"Can be purchased",
                         required=True, 
                         default=True,
                         readonly=True)

    PurchaseCutOffDate = DateTime(title=u"Purchase cutoff date",
                                  required=False)

    VendorInfo = Object(IPurchasableVendorInfo,
                        title=u"vendor info", required=False)
    VendorInfo.setTaggedValue('_ext_excluded_out', True)

    def isPublic():
        """
        return if this purchasable is public
        """


class IPurchasableChoiceBundle(IPurchasable):
    """
    marker interface for a purchasable choice bundle.

    Buyers can buy/redeem one item from the Items list.
    """

import zope.deferredimport
zope.deferredimport.initialize()
zope.deferredimport.deprecatedFrom(
    "Moved to nti.app.products.courseware_store.interfaces",
    "nti.app.products.courseware_store.interfaces",
    "ICourse",
    "IPurchasableCourse",
    "IPurchasableCourseChoiceBundle"
)


class ICopier(interface.Interface):
    """
    An adapter to an object that is being copied
    """

    def __call__(source, *args, **kwargs):
        """
        Given the source object return a new copy.
        """


class IPrice(interface.Interface):

    Amount = Number(title=u"The price amount", required=True)

    Currency = ValidTextLine(title=u"The currency",
                             required=False,
                             default=u'USD')


class IPriceable(interface.Interface):

    NTIID = TextLine(title=u'Purchasable item NTTID', required=True)

    Quantity = Int(title=u"Quantity", 
                   required=False,
                   default=1,
                   min=0)

    def copy():
        """
        makes a new copy of this priceable
        """


class IPurchaseItem(IPriceable):
    """
    marker interface for a purchase order item
    """


class IPurchaseOrder(IMinimalSequence):
    Items = ListOrTuple(value_type=Object(IPriceable), title=u'The items',
                        required=True, min_length=1)

    Quantity = Int(title=u'Purchase bulk quantity (overwrites-item quantity)',
                   required=False)

    NTIIDs = interface.Attribute(u"Purchasable NTIIDs")
    NTIIDs.setTaggedValue('_ext_excluded_out', True)

    def copy(purchasables=None):
        """
        makes a new copy of this purchase order

        :param purchasables Collection of purchasables to copy. None/Empty copy all
        """


class IPricedItem(IPriceable):

    PurchaseFee = Number(title=u"Fee Amount", required=False)
    PurchaseFee.setTaggedValue('_ext_excluded_out', True)

    PurchasePrice = Number(title=u"Cost amount", required=True)

    NonDiscountedPrice = Number(title=u"Non discounted price", 
                                required=False)

    Currency = ValidTextLine(title=u'Currency ISO code',
                             required=True,
                             default=u'USD')


class IPricingResults(interface.Interface):

    Items = ListOrTuple(value_type=Object(IPricedItem), 
                        title=u'The priced items',
                        required=True, min_length=0)

    TotalPurchaseFee = Number(title=u"Fee Amount", required=False)
    TotalPurchaseFee.setTaggedValue('_ext_excluded_out', True)

    TotalPurchasePrice = Number(title=u"Cost amount", 
                                required=True)

    TotalNonDiscountedPrice = Number(title=u"Non discounted price",
                                     required=False)

    Currency = ValidTextLine(title=u'Currency ISO code',
                             required=True, 
                             default=u'USD')


class IUserAddress(interface.Interface):

    Street = ValidText(title=u'Street address', required=False)

    City = ValidTextLine(title=u'The city name', required=False)

    State = ValidTextLine(title=u'The state', required=False)

    Zip = ValidTextLine(title=u'The zip code',
                        required=False, 
                        default=u'')

    Country = ValidTextLine(title=u'The country',
                            required=False, 
                            default=u'USA')


class IPaymentCharge(interface.Interface):

    Amount = Number(title=u"Change amount", 
                    required=True)

    Created = Number(title=u"Created timestamp",
                     required=True)

    Currency = ValidTextLine(title=u'Currency amount',
                             required=True, 
                             default=u'USD')

    CardLast4 = Int(title=u'CreditCard last 4 digits', 
                    required=False)

    Name = ValidTextLine(title=u'The customer/charge name',
                        required=False)

    Address = Object(IUserAddress, 
                     title=u'User address', 
                     required=False)


class IOperationError(interface.Interface):
    Type = TextLine(title=u'Error type', required=True)

    Code = TextLine(title=u'Error code', required=False)

    Message = ValidText(title=u'Error message', 
                        required=True)


class IPricingError(IOperationError):
    pass


class IPurchaseError(IOperationError):
    pass


class IRefundError(IOperationError):
    pass


class IRedemptionError(IOperationError):
    pass


class INTIStoreException(interface.Interface):
    """
    interface for store exceptions
    """


class IPurchaseException(INTIStoreException):
    """
    interface for purchase exceptions
    """


class IPricingException(INTIStoreException):
    """
    interface for pricing exceptions
    """


class IRefundException(INTIStoreException):
    """
    interface for refund exceptions
    """


class IRedemptionException(INTIStoreException):
    """
    interface for redeeem exceptions
    """


class IPurchasablePricer(interface.Interface):

    def price(priceable, registry=None):
        """
        price the specfied priceable
        """

    def evaluate(priceables, registry=None):
        """
        price the specfied priceables
        """


class IPaymentProcessor(interface.Interface):

    name = ValidTextLine(title=u'Processor name', required=True)

    def validate_coupon(coupon):
        """
        validate the specified coupon
        """

    def apply_coupon(amount, coupon):
        """
        apply the specified coupon to the specified amout
        """

    def process_purchase(purchase, username, expected_amount=None):
        """
        Process a purchase attempt

        :purchase purchase identifier
        :username User making the purchase
        :expected_amount: expected amount
        """

    def refund_purchase(purchase, amount=None):
        """
        Refund a purchase attempt

        :purchase purchase identifier
        :amount: expected amount
        """

    def sync_purchase(purchase_id, username):
        """
        Synchronized the purchase data with the payment processor info

        :purchase purchase identifier
        :user User that made the purchase
        """


class IPurchaseAttemptContext(IEnumerableMapping):
    """
    Arbitrary purchase attempt information

    This is simply a dictionary and this module does not define
    the structure of it.
    """


class IPurchaseAttempt(IContained):

    Processor = Choice(vocabulary=PAYMENT_PROCESSORS_VOCABULARY,
                       title=u'purchase processor',
                       required=True)

    State = Choice(vocabulary=PA_STATE_VOCABULARY, 
                   title=u'Purchase state',
                   required=True)

    Order = Object(IPurchaseOrder, 
                   title=u"Purchase order", 
                   required=True)

    Description = ValidTextLine(title=u'A purchase description',
                                required=False)

    StartTime = Number(title=u'Start time', required=True)

    EndTime = Number(title=u'Completion time', required=False)

    Pricing = Object(IPricingResults, 
                     title=u'Pricing results',
                     required=False)

    Error = Object(IOperationError, 
                   title=u'Error object',
                   required=False)

    Synced = Bool(title=u'if the item has been synchronized with the processors data',
                  required=True, 
                  default=False)

    Context = Object(IPurchaseAttemptContext, 
                     title=u"Purchase attempt context",
                     required=False)
    Context.setTaggedValue('_ext_excluded_out', True)

    # CS. these fields are readonly and must not be created
    Items = interface.Attribute(u"Purchasable NTIIDs")
    Items.setTaggedValue('_ext_excluded_out', True)

    Profile = interface.Attribute('user profile')
    Profile.setTaggedValue('_ext_excluded_out', True)

    def has_completed():
        """
        return if the purchase has completed
        """

    def has_failed():
        """
        return if the purchase has failed
        """

    def has_succeeded():
        """
        return if the purchase has been successful
        """

    def is_unknown():
        """
        return if state of the purchase is unknown
        """

    def is_pending():
        """
        return if the purchase is pending (started)
        """

    def is_refunded():
        """
        return if the purchase has been refunded
        """

    def is_disputed():
        """
        return if the purchase has been disputed
        """

    def is_reserved():
        """
        return if the purchase has been reserved with the processor
        """

    def is_canceled():
        """
        return if the purchase has been canceled
        """

    def is_synced():
        """
        return if the purchase has been synchronized with the payment processor
        """


class IInvitationPurchaseAttempt(IPurchaseAttempt):

    ExpirationTime = Number(title=u"The expirtation time", 
                            required=False)

    def isExpired(now=None):
        """
        return if this invitation is expired
        """


class IRedeemedPurchaseAttempt(IPurchaseAttempt):
    RedemptionTime = Number(title=u'Redemption time', 
                            required=True)

    RedemptionCode = TextLine(title=u'Redemption Code', 
                              required=True)

    SourcePurchaseID = TextLine(title=u'Source Purchase ID', 
                                required=False)


class IGiftPurchaseAttempt(IPurchaseAttempt):
    Creator = ValidTextLine(title=u"Gift creator Email", required=True)

    SenderName = ValidTextLine(title=u'Sender name', required=False)

    Receiver = ValidTextLine(title=u'Receiver Email/username',
                             required=False,
                             constraint=checkEmailAddress)

    ReceiverName = ValidTextLine(title=u'Receiver name', 
                                 required=False)

    Message = ValidText(title=u'Gift message', 
                        required=False)

    TargetPurchaseID = TextLine(title=u'NTIID of target purchase',
                                required=False)
    TargetPurchaseID.setTaggedValue('_ext_excluded_out', True)

    DeliveryDate = Datetime(title=u"The gift delivery date", 
                            required=False)

    Sender = interface.Attribute(u"Alias for Creator")
    Sender.setTaggedValue('_ext_excluded_out', True)

    From = interface.Attribute(u"alias for Creator")
    From.setTaggedValue('_ext_excluded_out', True)

    To = interface.Attribute(u"alias for Receiver Name")
    To.setTaggedValue('_ext_excluded_out', True)

    def is_redeemed():
        """
        return if the purchase has been redeemed
        """


class IPurchaseAttemptFactory(interface.Interface):
    """
    Interface to create :class:`IPurchaseAttempt` objects.

    This factory are usually registered based the provider of the
    purchasable(s) being bought
    """

    def create(order, processor, state=None, description=None, start_time=None,
               context=None):
        """
        :param order: a :class:`IPurchaseOrder` object.
        :param processor: A payment processor name
        :param description: Purchase attempt description'
        :param start_time: Purchase attempt start time
        :param start_time: a :class:`IPurchaseAttemptContext` object.
        """


class IPurchaseAttemptEvent(IObjectEvent):
    object = Object(IPurchaseAttempt, title=u"The purchase")


class IPurchaseAttemptSynced(IPurchaseAttemptEvent):
    pass


class IPurchaseAttemptVoided(IPurchaseAttemptEvent):
    pass


class IPurchaseAttemptStateEvent(IPurchaseAttemptEvent):
    state = interface.Attribute(u'Purchase state')


class IPurchaseAttemptStarted(IPurchaseAttemptStateEvent):
    pass


class IPurchaseAttemptSuccessful(IPurchaseAttemptStateEvent):
    charge = interface.Attribute(u'Purchase charge')
    request = interface.Attribute(u'Purchase pyramid request')


class IPurchaseAttemptRefunded(IPurchaseAttemptStateEvent):
    charge = interface.Attribute(u'Purchase charge')
    request = interface.Attribute(u'Purchase pyramid request')


class IPurchaseAttemptDisputed(IPurchaseAttemptStateEvent):
    pass


class IPurchaseAttemptReserved(IPurchaseAttemptStateEvent):
    pass


class IPurchaseAttemptFailed(IPurchaseAttemptStateEvent):
    error = interface.Attribute(u'Failure error')


class IGiftPurchaseAttemptRedeemed(IPurchaseAttemptEvent):
    user = Object(IUser, title=u"The gift receiver")
    code = TextLine(title=u"The gift code", required=False)
    request = interface.Attribute(u'Purchase request')


@interface.implementer(IPurchaseAttemptEvent)
class PurchaseAttemptEvent(ObjectEvent):

    @property
    def purchase(self):
        return self.object


@interface.implementer(IPurchaseAttemptSynced)
class PurchaseAttemptSynced(PurchaseAttemptEvent):
    pass


@interface.implementer(IPurchaseAttemptVoided)
class PurchaseAttemptVoided(PurchaseAttemptEvent):
    pass


@interface.implementer(IPurchaseAttemptStarted)
class PurchaseAttemptStarted(PurchaseAttemptEvent):
    state = PA_STATE_STARTED


@interface.implementer(IPurchaseAttemptSuccessful)
class PurchaseAttemptSuccessful(PurchaseAttemptEvent):

    state = PA_STATE_SUCCESS

    def __init__(self, purchase, charge=None, request=None):
        super(PurchaseAttemptSuccessful, self).__init__(purchase)
        self.charge = charge
        self.request = request


@interface.implementer(IPurchaseAttemptRefunded)
class PurchaseAttemptRefunded(PurchaseAttemptEvent):
    state = PA_STATE_REFUNDED

    def __init__(self, purchase, charge=None, request=None):
        super(PurchaseAttemptRefunded, self).__init__(purchase)
        self.charge = charge
        self.request = request


@interface.implementer(IPurchaseAttemptDisputed)
class PurchaseAttemptDisputed(PurchaseAttemptEvent):
    state = PA_STATE_DISPUTED


@interface.implementer(IPurchaseAttemptReserved)
class PurchaseAttemptReserved(PurchaseAttemptEvent):
    state = PA_STATE_RESERVED


@interface.implementer(IPurchaseAttemptFailed)
class PurchaseAttemptFailed(PurchaseAttemptEvent):

    error = None
    state = PA_STATE_FAILED

    def __init__(self, purchase, error=None):
        super(PurchaseAttemptFailed, self).__init__(purchase)
        self.error = error


@interface.implementer(IGiftPurchaseAttemptRedeemed)
class GiftPurchaseAttemptRedeemed(PurchaseAttemptEvent):

    state = PA_STATE_REDEEMED

    def __init__(self, purchase, user, code=None, request=None):
        super(GiftPurchaseAttemptRedeemed, self).__init__(purchase)
        self.user = user
        self.code = code
        self.request = request


class IRedeemedPurchaseAttemptRegistered(IPurchaseAttemptEvent):
    user = Object(IUser, title=u"The gift receiver")
    code = TextLine(title=u"The gift code", 
                    required=False)


@interface.implementer(IRedeemedPurchaseAttemptRegistered)
class RedeemedPurchaseAttemptRegistered(PurchaseAttemptEvent):

    def __init__(self, purchase, user, code=None):
        super(RedeemedPurchaseAttemptRegistered, self).__init__(purchase)
        self.user = user
        self.code = code


# user purchase history


class IPurchaseHistory(interface.Interface):

    def add_purchase(purchase):
        pass

    def remove_purchase(purchase):
        pass

    def get_purchase(pid):
        pass

    def get_purchase_state(pid):
        pass

    def get_purchase_history(start_time=None, end_time=None):
        pass

    def get_pending_purchases():
        pass

    def clear():
        pass

    def values():
        """
        Return all purchase attempts
        """

    def __iter__():
        """
        Return an iterator object.
        """


# invitations


class IPurchaseInvitation(IInvitation):
    source_purchase = Variant((TextLine(title=u"Purchase NTIID"),
                               Object(IPurchaseAttempt, title=u"The source purchase")),
                              title=u'The source purchase')

    redeemed_purchase = Variant((TextLine(title=u"Purchase NTIID"),
                                 Object(IRedeemedPurchaseAttempt, title=u"The linked purchase")),
                                title=u'The Linked purchase',
                                required=False)


class IPurchaseInvitationActor(IInvitationActor):
    """
    Actor for :class:``.IPurchaseInvitation`` objects
    """


class IStorePurchaseInvitation(IPurchaseInvitation):
    pass


class IStorePurchaseInvitationActor(IPurchaseInvitationActor):
    """
    Actor for :class:``.IStorePurchaseInvitation`` objects
    """


class IStoreGiftInvitation(IPurchaseInvitation):
    item = ValidTextLine(title=u"Purchase item NTIID", 
                         required=False)


class IStoreGiftInvitationActor(IPurchaseInvitationActor):
    """
    Actor for :class:``.IStoreGiftInvitation`` objects
    """


# gift registry


class IUserGiftHistory(IContained):
    pass


class IGiftRegistry(IContainer, IContained):
    """
    marker interface for gift registry.
    This object is registerd as a persistent utility
    """

    def register_purchase(username, purchase):
        pass

    def get_pending_purchases(username, items=None):
        pass


# transformer


class IObjectTransformer(interface.Interface):
    """
    Called to transform an object

    These are typically found as adapters, registered on the
    context object.

    The context object is passed to the ``__call__`` method to allow the adapter
    factories to return singleton objects such as a function.
    """

    def __call__(context, user=None):
        pass


# metadata


class IStorePurchaseMetadataProvider(interface.Interface):
    """
    Updates the given data dict with metadata information on
    the purchase/
    """

    def update_metadata(data):
        pass


# deprecated interfaces


deprecated('IEnrollmentAttempt', 'Use new course enrollment')
class IEnrollmentAttempt(IPurchaseAttempt):
    pass


deprecated('IEnrollmentPurchaseAttempt', 'Use new course enrollment')
class IEnrollmentPurchaseAttempt(IEnrollmentAttempt):
    Processor = ValidTextLine(title=u'Enrollment institution', 
                              required=False)
