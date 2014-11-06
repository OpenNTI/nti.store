#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import not_none
from hamcrest import has_length
from hamcrest import assert_that

import unittest
from functools import partial

from zope import component

from nti.dataserver.users import User
from nti.dataserver.interfaces import IDataserverTransactionRunner

from nti.store.store import get_purchase_attempt

from nti.store.purchase_order import create_purchase_item
from nti.store.purchase_order import create_purchase_order
from nti.store.purchase_attempt import create_gift_purchase_attempt

from nti.store.gift_registry import get_gift_purchase_attempt
from nti.store.gift_registry import get_gift_pending_purchases
from nti.store.gift_registry import remove_gift_purchase_attempt
from nti.store.gift_registry import register_gift_purchase_attempt

from nti.store.interfaces import PA_STATE_STARTED
from nti.store.interfaces import PA_STATE_SUCCESS

from nti.dataserver.tests import mock_dataserver
from nti.dataserver.tests.mock_dataserver import WithMockDSTrans

from nti.store.tests import SharedConfiguringTestLayer

class TestGiftRegistry(unittest.TestCase):

	layer = SharedConfiguringTestLayer

	@property
	def ds(self):
		return mock_dataserver.current_mock_ds
	
	def _create_user(self, username='nt@nti.com', password='temp001'):
		usr = User.create_user(self.ds, username=username, password=password)
		return usr

	def create_gift_attempt(self, creator, item=u'xyz-book', state=None):
		state = state or PA_STATE_STARTED
		item = create_purchase_item(item, 1)
		order = create_purchase_order(item, quantity=None)
		result = create_gift_purchase_attempt(order=order, processor='stripe', 
										  	  state=state, creator=creator)
		return result

	@WithMockDSTrans
	def test_store_gift(self):

		username = "ichigo@bleach.org"
		
		with mock_dataserver.mock_db_trans(self.ds):
			attempt = self.create_gift_attempt(username)
			pid = register_gift_purchase_attempt(username, attempt)
			assert_that(pid, is_(not_none()))
			
		with mock_dataserver.mock_db_trans(self.ds):
			attempt = get_gift_purchase_attempt(pid)
			assert_that(attempt, is_(not_none()))
			
		with mock_dataserver.mock_db_trans(self.ds):
			attempt = get_purchase_attempt(pid) 
			assert_that(attempt, is_(not_none()))

		pending = get_gift_pending_purchases(username)
		assert_that(pending, has_length(1))
		
		transaction_runner = component.getUtility(IDataserverTransactionRunner)
		get_purchase = partial(get_purchase_attempt, 
							   purchase_id=pid)
		attempt = transaction_runner(get_purchase)
		assert_that(attempt, is_(not_none()))
		
		with mock_dataserver.mock_db_trans(self.ds):
			attempt.state = PA_STATE_SUCCESS
		
		pending = get_gift_pending_purchases(username)
		assert_that(pending, has_length(0))
		
		removal = remove_gift_purchase_attempt(pid, username)
		assert_that(removal, is_(True))

