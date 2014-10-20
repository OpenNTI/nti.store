#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import none
from hamcrest import is_not
from hamcrest import assert_that
from hamcrest import has_property

import unittest

from zope.event import notify

from nti.dataserver.users import User

from nti.store import RedeemException

from nti.store.interfaces import PA_STATE_STARTED
from nti.store.interfaces import PA_STATE_SUCCESS
from nti.store.interfaces import PA_STATE_UNKNOWN 
from nti.store.interfaces import PA_STATE_REFUNDED
from nti.store.interfaces import PA_STATE_REDEEMED

from nti.store.interfaces import PurchaseAttemptStarted
from nti.store.interfaces import PurchaseAttemptRefunded
from nti.store.interfaces import PurchaseAttemptSuccessful
from nti.store.interfaces import IInvitationPurchaseAttempt
from nti.store.interfaces import GiftPurchaseAttemptRedeemed

from nti.store.invitations import get_invitation_code

from nti.store.purchase_order import create_purchase_item
from nti.store.purchase_order import create_purchase_order
from nti.store.purchase_history import get_purchase_attempt
from nti.store.purchase_attempt import create_purchase_attempt
from nti.store.purchase_history import register_purchase_attempt
from nti.store.gift_registry import register_gift_purchase_attempt
from nti.store.purchase_attempt import create_gift_purchase_attempt
from nti.store.purchase_attempt import create_redeemed_purchase_attempt

from nti.dataserver.tests.mock_dataserver import WithMockDSTrans

from nti.store.tests import SharedConfiguringTestLayer

class TestEvents(unittest.TestCase):

	layer = SharedConfiguringTestLayer

	def _create_user(self, username='nt@nti.com', password='temp001'):
		usr = User.create_user(self.ds, username=username, password=password)
		return usr

	def _create_purchase_attempt(self, item=None, quantity=None, state=None, user=None):
		item = item or u'iid_3'
		item = create_purchase_item(item, 1)
		order = create_purchase_order(item, quantity=quantity)
		result = create_purchase_attempt(order, processor='stripe', state=state)
		if user is not None:
			register_purchase_attempt(result, user)
		return result
	
	def create_gift_attempt(self, creator, item=u'xyz-book', state=None):
		state = state or PA_STATE_STARTED
		item = create_purchase_item(item, 1)
		order = create_purchase_order(item, quantity=None)
		result = create_gift_purchase_attempt(order=order, processor='stripe', 
										  	  state=state, creator=creator)
		return result
	
	@WithMockDSTrans
	def test_started(self):
		pa = self._create_purchase_attempt(state=PA_STATE_UNKNOWN)
		notify(PurchaseAttemptStarted(pa))
		assert_that(pa, has_property('State', is_(PA_STATE_STARTED)))
		
		pa = self._create_purchase_attempt(quantity=5, state=PA_STATE_UNKNOWN)
		assert_that(IInvitationPurchaseAttempt.providedBy(pa), is_(True))
		notify(PurchaseAttemptStarted(pa))
		assert_that(pa, has_property('State', is_(PA_STATE_STARTED)))
		
	@WithMockDSTrans
	def test_success(self):
		user = self._create_user()
		pa = self._create_purchase_attempt(state=PA_STATE_STARTED, user=user)
		notify(PurchaseAttemptSuccessful(pa))
		assert_that(pa, has_property('State', is_(PA_STATE_SUCCESS)))
		
		pa = self._create_purchase_attempt(quantity=5, state=PA_STATE_STARTED, user=user)
		assert_that(IInvitationPurchaseAttempt.providedBy(pa), is_(True))
		notify(PurchaseAttemptSuccessful(pa))
		assert_that(pa, has_property('State', is_(PA_STATE_SUCCESS)))
		
	@WithMockDSTrans
	def test_simple_refund(self):
		user = self._create_user()
		pa = self._create_purchase_attempt(state=PA_STATE_SUCCESS, user=user)
		notify(PurchaseAttemptRefunded(pa))
		assert_that(pa, has_property('State', is_(PA_STATE_REFUNDED)))

	@WithMockDSTrans
	def test_invitation_refund(self):
		user = self._create_user()
		pa = self._create_purchase_attempt(state=PA_STATE_SUCCESS, user=user)
		inv = self._create_purchase_attempt(quantity=5, state=PA_STATE_SUCCESS, user=user)
		inv.register(user, pa.id)
		assert_that(inv.consume_token(), is_(True))
		assert_that(inv, has_property('tokens', is_(4)))
		notify(PurchaseAttemptRefunded(inv))
		assert_that(pa, has_property('State', is_(PA_STATE_REFUNDED)))
		assert_that(inv, has_property('State', is_(PA_STATE_REFUNDED)))
		assert_that(inv, has_property('tokens', is_(0)))
		
	@WithMockDSTrans
	def test_redeemed_refund(self):
		user = self._create_user()
		inv = self._create_purchase_attempt(quantity=5, state=PA_STATE_SUCCESS, user=user)
		code = get_invitation_code(inv)
		
		user2 = self._create_user(username="ichigo")
		rpa = create_redeemed_purchase_attempt(inv, code)
		new_pid = register_purchase_attempt(rpa, user2)

		inv.consume_token()
		inv.register(user2, new_pid)
		assert_that(inv, has_property('tokens', is_(4)))
		
		notify(PurchaseAttemptRefunded(rpa))
		
		assert_that(inv, has_property('tokens', is_(5)))		
		assert_that(rpa, has_property('State', is_(PA_STATE_REFUNDED)))
		
	@WithMockDSTrans
	def test_redeemed_gift(self):
		ichigo = 'ichigo@bleach.org'
		gift = self.create_gift_attempt(ichigo, state=PA_STATE_SUCCESS)
		gid = register_gift_purchase_attempt(ichigo, gift)
		assert_that(gid, is_not(none()))
		
		aizen = self._create_user(username="aizen")
		notify(GiftPurchaseAttemptRedeemed(gift, aizen))
		
		assert_that(gift, has_property('State', is_(PA_STATE_REDEEMED)))
		assert_that(gift, has_property('TargetPurchaseID', is_not(none())))
		
		pa = get_purchase_attempt(gift.TargetPurchaseID, aizen)
		assert_that(pa, has_property('creator', is_(aizen)))
		assert_that(pa, has_property('State', is_(PA_STATE_SUCCESS)))
		assert_that(pa, has_property('RedemptionCode', is_not(none())))

		with self.assertRaises(RedeemException):
			notify(GiftPurchaseAttemptRedeemed(gift, aizen))
	