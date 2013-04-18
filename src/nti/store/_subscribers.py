# -*- coding: utf-8 -*-
"""
Store event subscribers

$Id$
"""
from __future__ import print_function, unicode_literals, absolute_import
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import time

from zope import component

from nti.appserver.invitations import interfaces as invite_interfaces

from . import _content_roles
from . import purchasable_store
from . import interfaces as store_interfaces
from .purchase_history import remove_purchased_items
from .purchase_history import register_purchased_items

@component.adapter(store_interfaces.IPurchaseAttemptStarted)
def _purchase_attempt_started(event):
	purchase = event.object
	purchase.updateLastMod()
	purchase.State = store_interfaces.PA_STATE_STARTED
	logger.info('%s started' % purchase)

@component.adapter(store_interfaces.IPurchaseAttemptSuccessful)
def _purchase_attempt_successful(event):
	purchase = event.object
	purchase.updateLastMod()
	purchase.EndTime = time.time()
	purchase.State = store_interfaces.PA_STATE_SUCCESS
	register_purchased_items(purchase.creator, purchase.Items)

	# if not register invitation
	if not purchase.Quantity:
		# allow content roles
		lib_items = purchasable_store.get_content_items(purchase.Items)
		_content_roles._add_users_content_roles(purchase.creator, lib_items)

	logger.info('%s completed successfully' % purchase)

@component.adapter(store_interfaces.IPurchaseAttemptRefunded)
def _purchase_attempt_refunded(event):
	purchase = event.object
	purchase.updateLastMod()
	purchase.EndTime = time.time()
	purchase.State = store_interfaces.PA_STATE_REFUNDED
	remove_purchased_items(event.username, purchase.Items)

	# TODO: we need to handle when there is an invitation
	lib_items = purchasable_store.get_content_items(purchase.Items)
	_content_roles._remove_users_content_roles(event.username, lib_items)

	logger.info('%s has been refunded' % purchase)

@component.adapter(store_interfaces.IPurchaseAttemptDisputed)
def _purchase_attempt_disputed(event):
	purchase = event.object
	purchase.updateLastMod()
	purchase.State = store_interfaces.PA_STATE_DISPUTED
	logger.info('%s has been disputed' % purchase)

@component.adapter(store_interfaces.IPurchaseAttemptFailed)
def _purchase_attempt_failed(event):
	purchase = event.object
	purchase.updateLastMod()
	purchase.EndTime = time.time()
	purchase.State = store_interfaces.PA_STATE_FAILED
	if event.error_code:
		purchase.ErrorCode = event.error_code
	if event.error_message:
		purchase.ErrorMessage = unicode(event.error_message)

	logger.info('%s failed. %s' % (purchase, event.error_message))

@component.adapter(store_interfaces.IPurchaseAttemptSynced)
def _purchase_attempt_synced(event):
	purchase = event.object
	purchase.Synced = True
	logger.info('%s has been synched' % purchase)

@component.adapter(store_interfaces.IStorePurchaseInvitation, invite_interfaces.IInvitationAcceptedEvent)
def _purchase_invitation_accepted(invitation, event):
	pass
