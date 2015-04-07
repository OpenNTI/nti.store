#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import none
from hamcrest import is_not
from hamcrest import not_none
from hamcrest import has_length
from hamcrest import assert_that
from hamcrest import has_property

import unittest
from datetime import datetime

from nti.dataserver.users import User

from nti.store.purchase_order import create_purchase_item
from nti.store.purchase_order import create_purchase_order

from nti.store.purchase_attempt import create_purchase_attempt
from nti.store.purchase_attempt import create_gift_purchase_attempt

from nti.store.gift_registry import register_gift_purchase_attempt

from nti.store.interfaces import PA_STATE_SUCCESS
from nti.store.interfaces import PA_STATE_UNKNOWN

from nti.store.interfaces import IPurchaseHistory
from nti.store.predicates import _PurchaseAttemptPrincipalObjects
from nti.store.predicates import _GiftPurchaseAttemptPrincipalObjects

from nti.dataserver.tests.mock_dataserver import WithMockDSTrans

from nti.store.tests import SharedConfiguringTestLayer

class TestPurchaseAttempt(unittest.TestCase):

	layer = SharedConfiguringTestLayer

	processor = 'stripe'

	def _create_user(self, username='nt@nti.com', password='temp001'):
		usr = User.create_user(self.ds, username=username, password=password)
		return usr

	def _create_purchase_attempt(self, item=u'xyz', quantity=None, state=None,
								 context=None):
		state = state or PA_STATE_UNKNOWN
		purchase_item = create_purchase_item(item, 1)
		assert_that(hash(purchase_item), is_(not_none()))
		
		purchase_order = create_purchase_order(purchase_item, quantity=quantity)
		assert_that(hash(purchase_order), is_(not_none()))
		
		purchase = create_purchase_attempt(	purchase_order, 
										 	processor=self.processor,
										 	state=state,
										 	context=context)
		assert_that(hash(purchase), is_(not_none()))
		return purchase

	def create_gift_attempt(self, creator, item=u'xyz-book', state=None):
		state = state or PA_STATE_SUCCESS
		item = create_purchase_item(item, 1)
		order = create_purchase_order(item, quantity=None)
		result = create_gift_purchase_attempt(order=order, processor='stripe', 
										  	  state=state, creator=creator, 
										  	  sender='Ichigo Kurosaki',
										  	  receiver="azien@bleach.org",
										  	  receiver_name="Azien Sosuke",
										  	  delivery_date=datetime.now())
		return result

	@WithMockDSTrans
	def test_simple_purchase_attempt(self):
		purchase = self._create_purchase_attempt(state=PA_STATE_SUCCESS, 
												 context={"Ichigo":"Bleach"})
		assert_that(purchase, has_property('createdTime', is_not(none())))
		assert_that(purchase, has_property('StartTime', is_not(none())))
		assert_that(purchase, has_property('Processor', is_(self.processor)))
		assert_that(purchase, has_property('Description', is_(none())))
		assert_that(purchase, has_property('Order', is_not(none())))
		
		assert_that(purchase, has_property('state', is_(PA_STATE_SUCCESS)))
		assert_that(purchase, has_property('state', is_(PA_STATE_SUCCESS)))
		
		assert_that(purchase, has_property('context', has_length(1)))
		assert_that(purchase, has_property('Context', has_length(1)))
		
		assert_that(purchase, has_property('Items', is_((u'xyz',))))
		
		order = purchase.Order
		assert_that(order, has_length(1))
		assert_that(order, has_property('Quantity', is_(none())))
		assert_that(order, has_property('NTIIDs', is_((u'xyz',))))
		
		iterable = list(order)
		assert_that(iterable, has_length(1))
		
		item = order[0]
		assert_that(item, has_property('NTIID', is_('xyz')))
		assert_that(item, has_property('Quantity', is_(1)))
		
		user = self._create_user()
		hist = IPurchaseHistory(user)
		hist.add_purchase(purchase)
		
		assert_that(purchase, has_property('id', is_not(none())))
		assert_that(purchase, has_property('creator', is_(user)))
		assert_that(purchase, has_property('Creator', is_(user)))
		
		assert_that(purchase, has_property('profile', is_not(none())))
		assert_that(purchase, has_property('Profile', is_not(none())))

		predicate = _PurchaseAttemptPrincipalObjects(user)
		ids = list(predicate.iter_intids())
		assert_that(ids, has_length(1))

	@WithMockDSTrans
	def test_simple_gift_purchase_attempt(self):
		username = "ichigo@bleach.org"
		attempt = self.create_gift_attempt(username)
		register_gift_purchase_attempt(username, attempt)
		
		assert_that(attempt, has_property('createdTime', is_not(none())))
		assert_that(attempt, has_property('StartTime', is_not(none())))
		assert_that(attempt, has_property('Processor', is_(self.processor)))
		assert_that(attempt, has_property('Description', is_(none())))
		assert_that(attempt, has_property('Order', is_not(none())))
		
		assert_that(attempt, has_property('state', is_(PA_STATE_SUCCESS)))
		assert_that(attempt, has_property('state', is_(PA_STATE_SUCCESS)))
		
		assert_that(attempt, has_property('creator', is_(username)) )
		assert_that(attempt, has_property('Creator', is_(username)) )
		
		assert_that(attempt, has_property('To', is_('Azien Sosuke')) )
		assert_that(attempt, has_property('ReceiverName', is_('Azien Sosuke')) )
		assert_that(attempt, has_property('Receiver', is_('azien@bleach.org')) )
		
		assert_that(attempt, has_property('Sender', is_('Ichigo Kurosaki')) )
		assert_that(attempt, has_property('SenderName', is_('Ichigo Kurosaki')) )
	
		assert_that(attempt, has_property('DeliveryDate', is_not(none())) )
		
		predicate = _GiftPurchaseAttemptPrincipalObjects()
		ids = list(predicate.iter_intids())
		assert_that(ids, has_length(1))
