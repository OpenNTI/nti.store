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

# TODO: break this dep
from nti.appserver.invitations.interfaces import IInvitationAcceptedEvent

from . import invitations
from . import purchasable
from . import content_roles
from . import purchase_attempt
from . import purchase_history

from .interfaces import PA_STATE_FAILED
from .interfaces import PA_STATE_STARTED
from .interfaces import PA_STATE_SUCCESS
from .interfaces import PA_STATE_DISPUTED
from .interfaces import PA_STATE_REFUNDED
from .interfaces import IPurchaseAttemptFailed
from .interfaces import IPurchaseAttemptSynced
from .interfaces import IPurchaseAttemptStarted
from .interfaces import IPurchaseAttemptDisputed
from .interfaces import IPurchaseAttemptRefunded
from .interfaces import IRedeemedPurchaseAttempt
from .interfaces import IStorePurchaseInvitation
from .interfaces import IInvitationPurchaseAttempt
from .interfaces import IPurchaseAttemptSuccessful

def _update_state(purchase, state):
	if purchase is not None:
		purchase.updateLastMod()
		purchase.State = state
		lifecycleevent.modified(purchase)

@component.adapter(IPurchaseAttemptStarted)
def _purchase_attempt_started(event):
	purchase = event.object
	_update_state(purchase, PA_STATE_STARTED)
	logger.info('%r started' % purchase)

def _activate_items(purchase, user=None, add_roles=True):
	user = user or purchase.creator
	purchase_history.activate_items(user, purchase.Items)
	if add_roles:
		lib_items = purchasable.get_content_items(purchase.Items)
		content_roles.add_users_content_roles(user, lib_items)

@component.adapter(IPurchaseAttemptSuccessful)
def _purchase_attempt_successful(event):
	purchase = event.object
	purchase.EndTime = time.time()
	_update_state(purchase, PA_STATE_SUCCESS)

	# if not register invitation
	if not purchase.Quantity:
		_activate_items(purchase)
	
	logger.info('%r completed successfully', purchase.id)

def _return_items(purchase, user=None, remove_roles=True):
	if purchase is None:
		return
	user = user or purchase.creator
	purchase_history.deactivate_items(user, purchase.Items)
	if remove_roles:
		lib_items = purchasable.get_content_items(purchase.Items)
		content_roles.remove_users_content_roles(user, lib_items)

@component.adapter(IPurchaseAttemptRefunded)
def _purchase_attempt_refunded(event):
	purchase = event.object

	purchase.EndTime = time.time()
	_update_state(purchase, PA_STATE_REFUNDED)

	if IInvitationPurchaseAttempt.providedBy(purchase):
		# set all tokens to zero
		purchase.reset()
		# return all items from linked purchases (redemptions) and refund them
		for username, pid in purchase.consumerMap().items():
			p = purchase_history.get_purchase_attempt(pid)
			_return_items(p, username)
			_update_state(p, PA_STATE_REFUNDED)

	elif not purchase.Quantity:
		_return_items(purchase, purchase.creator)

	# return consumed token
	if IRedeemedPurchaseAttempt.providedBy(purchase):
		code = purchase.RedemptionCode
		p = invitations.get_purchase_by_code(code)
		if IInvitationPurchaseAttempt.providedBy(p):
			p.restore_token()

	logger.info('%r has been refunded', purchase)

@component.adapter(IPurchaseAttemptDisputed)
def _purchase_attempt_disputed(event):
	purchase = event.object
	_update_state(purchase, PA_STATE_DISPUTED)
	logger.info('%r has been disputed', purchase)

@component.adapter(IPurchaseAttemptFailed)
def _purchase_attempt_failed(event):
	purchase = event.object
	purchase.Error = event.error
	purchase.EndTime = time.time()
	_update_state(purchase, PA_STATE_FAILED)
	logger.info('%r failed. %s', purchase.id, purchase.Error)

@component.adapter(IPurchaseAttemptSynced)
def _purchase_attempt_synced(event):
	purchase = event.object
	purchase.Synced = True
	purchase.updateLastMod()
	lifecycleevent.modified(purchase)
	logger.info('%r has been synched' % purchase)

@component.adapter(IStorePurchaseInvitation, IInvitationAcceptedEvent)
def _purchase_invitation_accepted(invitation, event):
	if 	IStorePurchaseInvitation.providedBy(invitation) and \
		IInvitationPurchaseAttempt.providedBy(invitation.purchase):

		original = invitation.purchase

		# create and register a purchase attempt for accepting user
		rpa = purchase_attempt.create_redeemed_purchase_attempt(original, invitation.code)
		new_pid = purchase_history.register_purchase_attempt(rpa, event.user)
		purchase_history.activate_items(event.user, rpa.Items)

		# link purchase. This validates there are enough tokens and
		# use has not accepted already
		invitation.register(event.user, new_pid)

		# activate role(s)
		lib_items = purchasable.get_content_items(original.Items)
		content_roles.add_users_content_roles(event.user, lib_items)
