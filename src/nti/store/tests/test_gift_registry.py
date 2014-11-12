#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import none
from hamcrest import is_not
from hamcrest import has_key
from hamcrest import not_none
from hamcrest import has_entry
from hamcrest import has_length
from hamcrest import assert_that
from hamcrest import has_property
does_not = is_not

import unittest

from functools import partial

from zope import component

from nti.dataserver.users import User
from nti.dataserver.interfaces import IDataserverTransactionRunner

from nti.externalization.externalization import to_external_object

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
										  	  state=state, creator=creator, 
										  	  sender='Ichigo Kurosaki',
										  	  receiver="azien@bleach.org",
										  	  receiver_name="Azien Sosuke")
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
		
		with mock_dataserver.mock_db_trans(self.ds):
			ext = to_external_object(attempt)
			assert_that( ext, has_key('MimeType') )
			assert_that( ext, has_entry( 'Class', 'PurchaseAttempt') )
			assert_that( ext, has_entry( 'State', 'Success') )
			assert_that( ext, has_entry( 'OID', is_not(none())) )
			assert_that( ext, has_entry( 'Processor', is_not(none())) )
			assert_that( ext, has_entry( 'Last Modified', is_not(none())) )
			assert_that( ext, has_entry( 'StartTime', is_not(none())) )
			assert_that( ext, has_entry( 'EndTime', is_(none())) )
			assert_that( ext, has_entry( 'Creator', is_(username)) )
			assert_that( ext, has_entry( 'To', is_('Azien Sosuke')) )
			assert_that( ext, has_entry( 'Receiver', is_('azien@bleach.org')) )
			assert_that( ext, has_entry( 'ReceiverName', is_('Azien Sosuke')) )
			assert_that( ext, has_entry( 'Sender', is_('Ichigo Kurosaki')) )
			assert_that( ext, has_entry( 'SenderName', is_('Ichigo Kurosaki')) )
			assert_that( ext, has_entry( 'RedemptionCode', is_not(none())) )
			assert_that( ext, does_not(has_key('Items')) )
			assert_that( ext, does_not(has_key('Profile')) )
			
		with mock_dataserver.mock_db_trans(self.ds):
			attempt = get_purchase_attempt(pid) 
			assert_that( attempt, has_property('Profile', has_property('email', username)) )
			assert_that( attempt, has_property('Profile', has_property('realname', 'Ichigo Kurosaki')) )
			assert_that( attempt, has_property('Profile', has_property('alias', 'Ichigo Kurosaki')) )
						
		removal = remove_gift_purchase_attempt(pid, username)
		assert_that(removal, is_(True))

