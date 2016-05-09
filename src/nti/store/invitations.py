#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Store invitations

.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component
from zope import interface

from zope.intid.interfaces import IIntIds

from nti.common.integer_strings import to_external_string
from nti.common.integer_strings import from_external_string

from nti.common.proxy import removeAllProxies

from nti.externalization.oids import to_external_ntiid_oid

from nti.invitations.interfaces import InvitationExpiredError
from nti.invitations.interfaces import InvitationValidationError
from nti.invitations.interfaces import InvitationAlreadyAcceptedError

from nti.invitations.model import Invitation

from nti.ntiids.ntiids import find_object_with_ntiid

from nti.schema.fieldproperty import createDirectFieldProperties

from nti.store import MessageFactory as _

from nti.store import get_user

from nti.store.content_roles import add_users_content_roles

from nti.store.interfaces import IPurchaseAttempt
from nti.store.interfaces import IStorePurchaseInvitation 
from nti.store.interfaces import IStorePurchaseInvitationActor

from nti.store.purchasable import expand_purchase_item_ids

from nti.store.purchase_attempt import create_redeemed_purchase_attempt

from nti.store.purchase_history import activate_items
from nti.store.purchase_history import register_purchase_attempt

InvitationExpired = InvitationExpiredError # BWC
InvitationAlreadyAccepted = InvitationAlreadyAcceptedError # BWC

class InvitationCapacityExceeded(InvitationValidationError):
	__doc__ = _("The limit for this invitation code has been exceeded.")
	i18n_message = __doc__

@interface.implementer(IStorePurchaseInvitation)
class StorePurchaseInvitation(Invitation):
	createDirectFieldProperties(IStorePurchaseInvitation)

	_purchase = None
	_linked_purchase_id = None

	def __init__(self, purchase, **kwargs):
		super(StorePurchaseInvitation, self).__init__(**kwargs)
		self.purchase = purchase

	def _setPurchase(self, nv):
		if IPurchaseAttempt.providedBy(nv):
			self._purchase = to_external_ntiid_oid(nv)
		else:
			self._purchase = nv

	def _getPurchase(self):
		if self._purchase:
			return find_object_with_ntiid(self._purchase)
		return None
	purchase = property(_getPurchase, _setPurchase)
	
	def _setLinkedPurchase(self, nv):
		if IPurchaseAttempt.providedBy(nv):
			self._linked_purchase_id = to_external_ntiid_oid(nv)
		else:
			self._linked_purchase_id = nv

	def _getLinkedPurchase(self):
		if self._linked_purchase_id:
			return find_object_with_ntiid(self._linked_purchase_id)
		return None
	linked_purchase = property(_getLinkedPurchase, _setLinkedPurchase)

	@property
	def capacity(self):
		return self.purchase.Quantity

	def register(self, user, linked_purchase_id=None, now=None):
		if self.purchase.isExpired(now=now):
			raise InvitationExpired()

		if not self.purchase.register(user, linked_purchase_id):
			raise InvitationAlreadyAccepted()

		if not self.purchase.consume_token():
			raise InvitationCapacityExceeded()

	def accept(self, user):
		user = get_user(user)
		super(StorePurchaseInvitation, self).accept(user)
_StorePurchaseInvitation = StorePurchaseInvitation # BWC

def get_invitation_code(purchase, registry=component):
	if purchase is not None:
		iid = registry.getUtility(IIntIds).getId(removeAllProxies(purchase))
		__traceback_info__ = purchase, iid
		result = to_external_string(iid)
		return result
	return None

def get_purchase_by_code(code, registry=component):
	if code is not None:
		__traceback_info__ = code
		iid = from_external_string(code)
		result = registry.getUtility(IIntIds).queryObject(iid)
		return result
	return None

def create_store_purchase_invitation(purchase, receiver=None):
	result = StorePurchaseInvitation(purchase=purchase)
	result.expirationTime = getattr(purchase, 'ExpirationTime', None) or 0
	result.creator = getattr(purchase.creator, 'username', purchase.creator)  # sender
	result.receiver = receiver
	return result

def _make_redeem_purchase_attempt(user, original, code, activate_roles=True):
	# create and register a purchase attempt for accepting user
	redeemed = create_redeemed_purchase_attempt(original, code)
	result = register_purchase_attempt(redeemed, user)
	activate_items(user, redeemed.Items)
	# XXX Legacy. activate any content roles
	if activate_roles:
		lib_items = expand_purchase_item_ids(original.Items)
		add_users_content_roles(user, lib_items)
	return result

@interface.implementer(IStorePurchaseInvitationActor)
class StorePurchaseInvitationActor(object):

	def __init__(self, invitation=None):
		self.invitation = invitation

	def accept(self, user, invitation=None):
		result = True
		invitation = self.invitation if invitation is None else invitation
		purchase = invitation.purchase
		if purchase.isExpired():
			raise InvitationExpired(invitation)
		original = invitation.purchase

		# XXX This is the redemption code to be used to link back to the
		# invitaion purchase. See refund subscribers
		redemption_code = get_invitation_code(purchase)

		# create and register a purchase attempt for accepting user
		linked_purchase_id = _make_redeem_purchase_attempt(user,
														   original, 
														   redemption_code)

		if not purchase.register(user, linked_purchase_id):
			raise InvitationAlreadyAccepted(invitation)

		if not purchase.consume_token():
			raise InvitationCapacityExceeded(invitation)

		invitation.linked_purchase = linked_purchase_id

		logger.info('Invitation %s has been accepted with purchase %s',
					invitation.code, linked_purchase_id)

		return result
