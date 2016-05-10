#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import not_none
from hamcrest import assert_that

from nose.tools import assert_raises

import unittest

from nti.dataserver.users import User

from nti.store.interfaces import IPurchaseHistory
from nti.store.interfaces import IStorePurchaseInvitationActor

from nti.store.invitations import InvitationExpired
from nti.store.invitations import InvitationCapacityExceeded
from nti.store.invitations import create_store_purchase_invitation

from nti.store.purchase_order import create_purchase_item
from nti.store.purchase_order import create_purchase_order
from nti.store.purchase_attempt import create_purchase_attempt

from nti.dataserver.tests.mock_dataserver import WithMockDSTrans

from nti.store.tests import SharedConfiguringTestLayer

class TestInvitations(unittest.TestCase):

	layer = SharedConfiguringTestLayer

	processor = 'stripe'

	def _create_user(self, username='nt@nti.com', password='temp001'):
		usr = User.create_user(self.ds, username=username, password=password)
		return usr

	def _create_purchase_attempt(self, item=u'xyz-book', quantity=None, 
								 state=None, expiration=None):
		pi = create_purchase_item(item, 1)
		po = create_purchase_order(pi, quantity=quantity)
		pa = create_purchase_attempt(po, processor=self.processor, state=state,
									 expiration=expiration)
		return pa

	@WithMockDSTrans
	def test_create_invitation(self):
		user = self._create_user()

		hist = IPurchaseHistory(user, None)
		purchase = self._create_purchase_attempt(quantity=1)
		hist.add_purchase(purchase)

		invitation = create_store_purchase_invitation(purchase, 'nt2@nti.com')
		assert_that(invitation, is_(not_none()))
		assert_that(invitation.creator, is_(user.username))

		user2 = self._create_user(username='nt2@nti.com')
		actor = IStorePurchaseInvitationActor(invitation)
		actor.accept(user2, invitation)

		user3 = self._create_user(username='nt3@nti.com')
		with assert_raises(InvitationCapacityExceeded):
			actor = IStorePurchaseInvitationActor(invitation)
			actor.accept(user3, invitation)

	@WithMockDSTrans
	def test_create_invitation_expired(self):
		user = self._create_user()

		hist = IPurchaseHistory(user, None)
		purchase = self._create_purchase_attempt(quantity=1, expiration=1)
		hist.add_purchase(purchase)

		invitation = create_store_purchase_invitation(purchase, 'nt3@nti.com')
		user3 = self._create_user(username='nt3@nti.com')
		with assert_raises(InvitationExpired):
			actor = IStorePurchaseInvitationActor(invitation)
			actor.accept(user3, invitation)

	@WithMockDSTrans
	def test_restore_token(self):
		user = self._create_user()
		hist = IPurchaseHistory(user, None)
		purchase = self._create_purchase_attempt(quantity=5)
		hist.add_purchase(purchase)

		purchase.consume_token()
		assert_that(purchase.tokens, is_(4))
		purchase.restore_token()
		assert_that(purchase.tokens, is_(5))
