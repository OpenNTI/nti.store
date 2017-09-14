#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component
from zope import interface

from zope.intid.interfaces import IIntIds

from nti.externalization.integer_strings import to_external_string
from nti.externalization.integer_strings import from_external_string

from nti.externalization.proxy import removeAllProxies

from nti.invitations.interfaces import InvitationExpiredError
from nti.invitations.interfaces import InvitationValidationError
from nti.invitations.interfaces import InvitationAlreadyAcceptedError

from nti.invitations.model import Invitation

from nti.ntiids.ntiids import find_object_with_ntiid

from nti.ntiids.oids import to_external_ntiid_oid

from nti.property.property import alias

from nti.schema.fieldproperty import createDirectFieldProperties

from nti.store import MessageFactory as _

from nti.store.interfaces import IPurchaseAttempt
from nti.store.interfaces import IStorePurchaseInvitation
from nti.store.interfaces import IStorePurchaseInvitationActor

from nti.store.redeem import make_redeem_purchase_attempt

InvitationExpired = InvitationExpiredError  # BWC
InvitationAlreadyAccepted = InvitationAlreadyAcceptedError  # BWC


class InvitationCapacityExceeded(InvitationValidationError):
    __doc__ = _(u"The limit for this invitation code has been exceeded.")
    i18n_message = __doc__


@interface.implementer(IStorePurchaseInvitation)
class StorePurchaseInvitation(Invitation):
    createDirectFieldProperties(IStorePurchaseInvitation)

    mimeType = mime_type = 'application/vnd.nextthought.store.purchaseinvitation'

    target = alias('redeemed_purchase')
    purchase = source = alias('source_purchase')

    _source_purchase = None
    _redeemed_purchase = None

    def __init__(self, purchase, **kwargs):
        super(StorePurchaseInvitation, self).__init__(**kwargs)
        self.source_purchase = purchase

    def _getSourcePurchase(self):
        if self._source_purchase:
            return find_object_with_ntiid(self._source_purchase)
        return None

    def _setSourcePurchase(self, nv):
        if IPurchaseAttempt.providedBy(nv):
            self._source_purchase = to_external_ntiid_oid(nv)
        else:
            self._source_purchase = nv

    source_purchase = invitation_purchase = property(_getSourcePurchase,
                                                     _setSourcePurchase)

    def _getRedeemedPurchase(self):
        if self._redeemed_purchase:
            return find_object_with_ntiid(self._redeemed_purchase)
        return None

    def _setRedeemedPurchase(self, nv):
        if IPurchaseAttempt.providedBy(nv):
            self._redeemed_purchase = to_external_ntiid_oid(nv)
        else:
            self._redeemed_purchase = nv

    redeemed_purchase = linked_purchase = property(_getRedeemedPurchase,
                                                   _setRedeemedPurchase)
_StorePurchaseInvitation = StorePurchaseInvitation  # BWC


def get_invitation_code(purchase):
    if purchase is not None:
        iid = component.getUtility(IIntIds).getId(removeAllProxies(purchase))
        __traceback_info__ = purchase, iid
        result = to_external_string(iid)
        return result
    return None


def get_purchase_by_code(code):
    if code is not None:
        __traceback_info__ = code
        iid = from_external_string(code)
        result = component.getUtility(IIntIds).queryObject(iid)
        return result
    return None


def create_store_purchase_invitation(purchase, receiver):
    result = StorePurchaseInvitation(purchase=purchase)
    result.receiver = getattr(receiver, 'username', receiver)
    result.expirationTime = getattr(purchase, 'ExpirationTime', None) or 0
    result.creator = getattr(purchase.creator, 
                             'username', 
                             purchase.creator)  # sender
    return result


@interface.implementer(IStorePurchaseInvitationActor)
class StorePurchaseInvitationActor(object):

    def __init__(self, invitation=None):
        self.invitation = invitation

    def accept(self, user, invitation=None):
        result = True
        invitation = self.invitation if invitation is None else invitation
        purchase = invitation.source_purchase
        if purchase.isExpired():
            raise InvitationExpired(invitation)
        original = invitation.purchase

        # XXX This is the redemption code to be used to link back to the
        # invitaion purchase. See refund subscribers
        redemption_code = get_invitation_code(purchase)

        # create and register a purchase attempt for accepting user
        redeemed_purchase = make_redeem_purchase_attempt(user,
                                                         original,
                                                         redemption_code)

        if not purchase.register(user, redeemed_purchase):
            raise InvitationAlreadyAccepted(invitation)

        if not purchase.consume_token():
            raise InvitationCapacityExceeded(invitation)

        invitation.redeemed_purchase = redeemed_purchase

        logger.info('Invitation %s has been accepted with purchase %s',
                    invitation.code, redeemed_purchase)

        return result
