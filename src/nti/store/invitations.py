#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Store invitations

.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from . import MessageFactory as _

import zc.intid as zc_intid

from zope import component
from zope import interface

# TODO: remove dep from nti.appserver
from nti.appserver.invitations.interfaces import IInvitation
from nti.appserver.invitations.invitation import JoinEntitiesInvitation

from nti.externalization.integer_strings import to_external_string
from nti.externalization.integer_strings import from_external_string

from . import get_user

from .interfaces import IStorePurchaseInvitation

interface.alsoProvides(IStorePurchaseInvitation, IInvitation)

class InvitationCapacityExceeded(Exception):
	"""
	Raised when a user is attempting to accept an invitation whose capacity
	has been exceeded.
	"""
	i18n_message = _("The limit for this invitation code has been exceeded.")

class InvitationAlreadyAccepted(Exception):
	"""
	Raised when a user is attempting to accept an invitation more than once
	"""
	i18n_message = _("Invitation already accepted")

class InvitationExpired(Exception):
	"""
	Raised when a user is attempting to accept an expired invitation
	"""
	i18n_message = _("Invitation expired")
	
@interface.implementer(IStorePurchaseInvitation)
class _StorePurchaseInvitation(JoinEntitiesInvitation):

	def __init__(self, code, purchase):
		super(_StorePurchaseInvitation, self).__init__(code, ())
		self.purchase = purchase

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
		super(_StorePurchaseInvitation, self).accept(user)

def get_invitation_code(purchase, registry=component):
	if purchase is not None:
		iid = registry.getUtility(zc_intid.IIntIds).getId(purchase)
		__traceback_info__ = purchase, iid
		result = to_external_string(iid)
		return result
	return None

def get_purchase_by_code(code, registry=component):
	if code is not None:
		__traceback_info__ = code
		iid = from_external_string(code)
		result = registry.getUtility(zc_intid.IIntIds).queryObject(iid)
		return result
	return None

def create_store_purchase_invitation(purchase, code=None, registry=component):
	invitation_code = code if code else get_invitation_code(purchase, registry=registry)
	result = _StorePurchaseInvitation(invitation_code, purchase)
	result.creator = purchase.creator
	return result
