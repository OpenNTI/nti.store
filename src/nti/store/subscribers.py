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

from zope import lifecycleevent

from zope.event import notify

from zope.lifecycleevent.interfaces import IObjectRemovedEvent

from zope.proxy import removeAllProxies

# TODO: break this dep
from nti.appserver.invitations.interfaces import IInvitationAcceptedEvent

from nti.dataserver.interfaces import IUser

from . import RedemptionException

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
from .interfaces import PurchaseAttemptRefunded
from .interfaces import IPurchaseAttemptDisputed
from .interfaces import IPurchaseAttemptRefunded
from .interfaces import IRedeemedPurchaseAttempt
from .interfaces import IStorePurchaseInvitation
from .interfaces import IInvitationPurchaseAttempt
from .interfaces import IPurchaseAttemptSuccessful
from .interfaces import IGiftPurchaseAttemptRedeemed

from .content_roles import add_users_content_roles
from .content_roles import remove_users_content_roles

from .purchasable import expand_purchase_item_ids

from .purchase_attempt import create_redeemed_purchase_attempt

from .purchase_history import activate_items
from .purchase_history import deactivate_items
from .purchase_history import get_purchase_attempt
from .purchase_history import register_purchase_attempt

from .store import get_gift_code
from .store import get_invitation_code
from .store import get_purchase_by_code
from .store import get_purchase_history
from .store import get_transaction_code

def _update_state(purchase, state):
	if purchase is not None:
		purchase = removeAllProxies(purchase)
		purchase.updateLastMod()
		purchase.State = state
		lifecycleevent.modified(purchase)

@component.adapter(IPurchaseAttempt, IPurchaseAttemptStarted)
def _purchase_attempt_started(purchase, event):
	_update_state(purchase, PA_STATE_STARTED)
	logger.info('%s started', purchase.id)

def _activate_items(purchase, user=None, add_roles=True):
	user = user or purchase.creator
	activate_items(user, purchase.Items)
	if add_roles:
		lib_items = expand_purchase_item_ids(purchase.Items)
		add_users_content_roles(user, lib_items)

@component.adapter(IPurchaseAttempt, IPurchaseAttemptSuccessful)
def _purchase_attempt_successful(purchase, event):
	purchase.EndTime = time.time()
	_update_state(purchase, PA_STATE_SUCCESS)
	## CS: We are assuming a non null quantity is for a bulk purchase
	## Therefore we don't activate items
	if not purchase.Quantity:
		_activate_items(purchase)
	logger.info('%s completed successfully. Transaction code %s',
				purchase.id, get_transaction_code(purchase))

def _return_items(purchase, user=None, remove_roles=True):
	if purchase is not None:
		user = user or purchase.creator
		deactivate_items(user, purchase.Items)
		if remove_roles:
			lib_items = expand_purchase_item_ids(purchase.Items)
			remove_users_content_roles(user, lib_items)

@component.adapter(IPurchaseAttempt, IPurchaseAttemptRefunded)
def _purchase_attempt_refunded(purchase, event):
	purchase.EndTime = time.time()
	_update_state(purchase, PA_STATE_REFUNDED)
	if not purchase.Quantity:
		_return_items(purchase, purchase.creator)
	logger.info('%s has been refunded', purchase.id)

@component.adapter(IInvitationPurchaseAttempt, IPurchaseAttemptRefunded)
def _invitation_purchase_attempt_refunded(purchase, event):
	# set all tokens to zero
	purchase.reset()
	# return all items from linked purchases (redemptions) and refund them
	for username, pid in purchase.consumerMap.items():
		p = get_purchase_attempt(pid)
		_return_items(p, username)
		_update_state(p, PA_STATE_REFUNDED)
	logger.info('%s has been refunded', purchase.id)

@component.adapter(IRedeemedPurchaseAttempt, IPurchaseAttemptRefunded)
def _redeemed_purchase_attempt_refunded(purchase, event):
	code = purchase.RedemptionCode
	source = get_purchase_by_code(code)
	if IInvitationPurchaseAttempt.providedBy(source):
		source.restore_token()
	elif IGiftPurchaseAttempt.providedBy(source):
		_return_items(purchase, purchase.creator)
		# change the state to success to be able to be given again
		source.TargetPurchaseID = None
		_update_state(source, PA_STATE_SUCCESS)
	logger.info('%s has been refunded', purchase.id)

@component.adapter(IPurchaseAttempt, IPurchaseAttemptDisputed)
def _purchase_attempt_disputed(purchase, event):
	_update_state(purchase, PA_STATE_DISPUTED)
	logger.info('%s has been disputed', purchase.id)

@component.adapter(IPurchaseAttempt, IPurchaseAttemptFailed)
def _purchase_attempt_failed(purchase, event):
	purchase.Error = event.error
	purchase.EndTime = time.time()
	_update_state(purchase, PA_STATE_FAILED)
	logger.warn('%s failed. %s', purchase.id, purchase.Error)

@component.adapter(IPurchaseAttempt, IPurchaseAttemptSynced)
def _purchase_attempt_synced(purchase, event):
	purchase = removeAllProxies(purchase)
	purchase.Synced = True
	purchase.updateLastMod()
	lifecycleevent.modified(purchase)
	logger.info('%s has been synched', purchase.id)

def _make_redeem_purchase_attempt(user, original, code, activate_roles=True):
	# create and register a purchase attempt for accepting user
	redeemed = create_redeemed_purchase_attempt(original, code)
	result = register_purchase_attempt(redeemed, user)
	activate_items(user, redeemed.Items)
	if activate_roles:
		lib_items = expand_purchase_item_ids(original.Items)
		add_users_content_roles(user, lib_items)
	return result

@component.adapter(IInvitationAcceptedEvent)
def _purchase_invitation_accepted(event):
	invitation = event.object
	if 	IStorePurchaseInvitation.providedBy(invitation) and \
		IInvitationPurchaseAttempt.providedBy(invitation.purchase):

		user = event.user
		code = invitation.code
		original = invitation.purchase

		# create and register a purchase attempt for accepting user
		new_pid = _make_redeem_purchase_attempt(user, original, code)

		# link purchase. This validates there are enough tokens and
		# use has not accepted already
		invitation.register(user, new_pid)

		logger.info('invitation %s has been accepted with purchase %s',
					code, new_pid)

@component.adapter(IGiftPurchaseAttempt, IPurchaseAttemptSuccessful)
def _gift_purchase_attempt_successful(purchase, event):
	logger.info('Gift purchase by %s completed successfully. Gift code %s',
				purchase.Creator, get_gift_code(purchase))

@component.adapter(IGiftPurchaseAttempt, IGiftPurchaseAttemptRedeemed)
def _gift_purchase_attempt_redeemed(purchase, event):
	if purchase.is_redeemed():
		raise RedemptionException("Gift purchase already redeemed")

	code = event.code or get_invitation_code(purchase)
	new_pid = _make_redeem_purchase_attempt(user=event.user, 
											original=purchase,
											code=code)

	## change state
	purchase = removeAllProxies(purchase)
	purchase.State = PA_STATE_REDEEMED
	purchase.TargetPurchaseID = new_pid
	purchase.updateLastMod()
	lifecycleevent.modified(purchase)
	logger.info('%s has been redeemed', purchase.id)

@component.adapter(IGiftPurchaseAttempt, IPurchaseAttemptRefunded)
def _gift_purchase_attempt_refunded(purchase, event):
	target = purchase.TargetPurchaseID
	if target:
		attempt = get_purchase_attempt(target)
		if attempt is not None and not attempt.is_refunded():
			notify(PurchaseAttemptRefunded(attempt))
	# update state in case other subscribers change it
	_update_state(purchase, PA_STATE_REFUNDED)
	logger.info('%s has been refunded', purchase.id)

@component.adapter(IUser, IObjectRemovedEvent)
def _on_user_removed(user, event):
	logger.info("Removing purchase data for user %s", user)
	history = get_purchase_history(user, safe=False)
	if history is not None:
		history.clear()
