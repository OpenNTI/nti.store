#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Store event subscribers

.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import time

from zope import component
from zope.event import notify
from zope import lifecycleevent

# TODO: break this dep
from nti.appserver.invitations.interfaces import IInvitationAcceptedEvent

from . import RedeemException

from .interfaces import PA_STATE_FAILED
from .interfaces import PA_STATE_STARTED
from .interfaces import PA_STATE_SUCCESS
from .interfaces import PA_STATE_DISPUTED
from .interfaces import PA_STATE_REDEEMED
from .interfaces import PA_STATE_REFUNDED

from .interfaces import IPurchaseAttempt
from .interfaces import IGiftPurchaseAttempt
from .interfaces import IPurchaseAttemptFailed
from .interfaces import IPurchaseAttemptSynced
from .interfaces import IPurchaseAttemptStarted
from .interfaces import IPurchaseAttemptDisputed
from .interfaces import IPurchaseAttemptRefunded
from .interfaces import IRedeemedPurchaseAttempt
from .interfaces import IStorePurchaseInvitation
from .interfaces import IInvitationPurchaseAttempt
from .interfaces import IPurchaseAttemptSuccessful
from .interfaces import IGiftPurchaseAttemptRedeemed

from .content_roles import add_users_content_roles
from .content_roles import remove_users_content_roles

from .invitations import get_invitation_code
from .invitations import get_purchase_by_code

from .purchasable import get_content_items

from .purchase_attempt import create_redeemed_purchase_attempt

from .purchase_history import activate_items
from .purchase_history import deactivate_items
from .purchase_history import get_purchase_attempt
from .purchase_history import register_purchase_attempt

def _update_state(purchase, state):
	if purchase is not None:
		purchase.updateLastMod()
		purchase.State = state
		lifecycleevent.modified(purchase)

@component.adapter(IPurchaseAttempt, IPurchaseAttemptStarted)
def _purchase_attempt_started(purchase, event):
	_update_state(purchase, PA_STATE_STARTED)
	logger.info('%r started' % purchase)

def _activate_items(purchase, user=None, add_roles=True):
	user = user or purchase.creator
	activate_items(user, purchase.Items)
	if add_roles:
		lib_items = get_content_items(purchase.Items)
		add_users_content_roles(user, lib_items)

@component.adapter(IPurchaseAttempt, IPurchaseAttemptSuccessful)
def _purchase_attempt_successful(purchase, event):
	purchase.EndTime = time.time()
	_update_state(purchase, PA_STATE_SUCCESS)
	## CS: We are assuming a non null quantity is for a bulk purchase
	## Therefore we don't activate items
	if not purchase.Quantity:
		_activate_items(purchase)
	logger.info('%r completed successfully', purchase.id)

def _return_items(purchase, user=None, remove_roles=True):
	if purchase is not None:
		user = user or purchase.creator
		deactivate_items(user, purchase.Items)
		if remove_roles:
			lib_items = get_content_items(purchase.Items)
			remove_users_content_roles(user, lib_items)

@component.adapter(IPurchaseAttempt, IPurchaseAttemptRefunded)
def _purchase_attempt_refunded(purchase, event):
	purchase.EndTime = time.time()
	_update_state(purchase, PA_STATE_REFUNDED)
	if not purchase.Quantity:
		_return_items(purchase, purchase.creator)
	logger.info('%r has been refunded', purchase)

@component.adapter(IInvitationPurchaseAttempt, IPurchaseAttemptRefunded)
def _invitation_purchase_attempt_refunded(purchase, event):
	# set all tokens to zero
	purchase.reset()
	# return all items from linked purchases (redemptions) and refund them
	for username, pid in purchase.consumerMap().items():
		p = get_purchase_attempt(pid)
		_return_items(p, username)
		_update_state(p, PA_STATE_REFUNDED)

@component.adapter(IRedeemedPurchaseAttempt, IPurchaseAttemptRefunded)
def _redeemed_purchase_attempt_refunded(purchase, event):
	code = purchase.RedemptionCode
	source = get_purchase_by_code(code)
	if IInvitationPurchaseAttempt.providedBy(source):
		source.restore_token()
	elif IGiftPurchaseAttempt.providedBy(source):
		_return_items(purchase, purchase.creator)
		# change the state to success to be able to be given again
		_update_state(source, PA_STATE_SUCCESS)

@component.adapter(IPurchaseAttempt, IPurchaseAttemptDisputed)
def _purchase_attempt_disputed(purchase, event):
	_update_state(purchase, PA_STATE_DISPUTED)
	logger.info('%r has been disputed', purchase)

@component.adapter(IPurchaseAttempt, IPurchaseAttemptFailed)
def _purchase_attempt_failed(purchase, event):
	purchase.Error = event.error
	purchase.EndTime = time.time()
	_update_state(purchase, PA_STATE_FAILED)
	logger.info('%r failed. %s', purchase.id, purchase.Error)

@component.adapter(IPurchaseAttempt, IPurchaseAttemptSynced)
def _purchase_attempt_synced(purchase, event):
	purchase.Synced = True
	purchase.updateLastMod()
	lifecycleevent.modified(purchase)
	logger.info('%r has been synched' % purchase)

def _redeem_purchase_attempt(user, original, code, activate_roles=True):
	# create and register a purchase attempt for accepting user
	redeemed = create_redeemed_purchase_attempt(original, code)
	result = register_purchase_attempt(redeemed, user)
	activate_items(user, redeemed.Items)
	if activate_roles:
		lib_items = get_content_items(original.Items)
		add_users_content_roles(user, lib_items)
	return result
		
@component.adapter(IStorePurchaseInvitation, IInvitationAcceptedEvent)
def _purchase_invitation_accepted(invitation, event):
	if 	IStorePurchaseInvitation.providedBy(invitation) and \
		IInvitationPurchaseAttempt.providedBy(invitation.purchase):

		user = event.user
		code = invitation.code
		original = invitation.purchase

		# create and register a purchase attempt for accepting user
		new_pid = _redeem_purchase_attempt(user, original, code)
		
		# link purchase. This validates there are enough tokens and
		# use has not accepted already
		invitation.register(user, new_pid)

@component.adapter(IGiftPurchaseAttempt, IGiftPurchaseAttemptRedeemed)
def _gift_purchase_attempt_redeemed(purchase, event):
	if purchase.is_redeemed():
		raise RedeemException("Gift purchase already redeemded")
	
	# create  and register a purchase attempt for accepting user
	code = get_invitation_code(purchase)
	new_pid = _redeem_purchase_attempt(event.user, purchase, code)
	
	# change state
	purchase.State = PA_STATE_REDEEMED
	purchase.TargetPurchaseID = new_pid
	purchase.updateLastMod()
	lifecycleevent.modified(purchase)
	logger.info('%r has been redeemed' % purchase)

from .interfaces import PurchaseAttemptRefunded

@component.adapter(IGiftPurchaseAttempt, IPurchaseAttemptRefunded)
def _gift_purchase_attempt_refunded(purchase, event):
	target = purchase.TargetPurchaseID
	if target:
		pa = get_purchase_attempt(target)
		if pa is not None and not pa.is_refunded():
			notify(PurchaseAttemptRefunded(pa))
	# update state in case other subscribers change it
	_update_state(purchase, PA_STATE_REFUNDED)
