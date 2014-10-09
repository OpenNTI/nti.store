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

import stripe
import unittest

from nti.dataserver.users import User

from nti.store.purchase_order import create_purchase_item
from nti.store.purchase_order import create_purchase_order
from nti.store.purchase_attempt import create_purchase_attempt

from nti.store.payments.stripe import StripeException
from nti.store.payments.stripe.interfaces import IStripeCustomer
from nti.store.payments.stripe.interfaces import IStripePurchaseError
from nti.store.payments.stripe.interfaces import IStripeOperationError
from nti.store.payments.stripe.interfaces import IStripePurchaseAttempt

import nti.dataserver.tests.mock_dataserver as mock_dataserver
from nti.dataserver.tests.mock_dataserver import WithMockDSTrans

from nti.store.tests import SharedConfiguringTestLayer

from nti.testing.matchers import verifiably_provides

class TestStripeAdapters(unittest.TestCase):

	layer = SharedConfiguringTestLayer

	processor = 'stripe'

	def _create_user(self, username='nt@nti.com', password='temp001'):
		ds = mock_dataserver.current_mock_ds
		usr = User.create_user(ds, username=username, password=password)
		return usr

	@WithMockDSTrans
	def test_stripe_customer_adapter(self):
		user = self._create_user()
		adapted = IStripeCustomer(user)
		assert_that(adapted, is_not(None))
		assert_that(adapted.customer_id, is_(None))

		adapted.Charges.add('ch_id')
		assert_that('ch_id' in adapted, is_(True))

		adapted.customer_id = 'xyz'
		assert_that(adapted.customer_id, is_('xyz'))

	def _create_purchase_attempt(self, item=u'xyz-book', quantity=None, state=None,
								 description='my purchase'):
		pi = create_purchase_item(item, 1)
		po = create_purchase_order(pi, quantity=quantity)
		result = create_purchase_attempt(po, processor=self.processor,
                                         description=description,
                                         state=state)
		return result

	@WithMockDSTrans
	def test_stripe_purchase_adapter(self):
		pa = self._create_purchase_attempt()
		adapted = IStripePurchaseAttempt(pa)
		adapted.charge_id = 'charge_id'
		adapted.token_id = 'token_id'
		assert_that(adapted.purchase, is_(pa))
		assert_that(adapted.charge_id, is_('charge_id'))
		assert_that(adapted.token_id, is_('token_id'))

	def test_exception_adapter(self):
		e = StripeException('my exception')
		adapted = IStripePurchaseError(e, None)
		assert_that(adapted, is_not(none()))
		assert_that(adapted.Type, is_('PurchaseError'))
		assert_that(adapted.Message, is_('my exception'))
		
	def test_stripe_error_adapters(self):
		e = stripe.CardError('my error', 'my param', 'my code')
		adapted = IStripeOperationError(e, None)
		assert_that(adapted, is_not(none()))
		assert_that(adapted.Type, is_('CardError'))
		assert_that(adapted.Message, is_('my error'))
		assert_that(adapted.Param, is_('my param'))
		assert_that(adapted.Code, is_('my code'))
		assert_that(adapted, verifiably_provides(IStripeOperationError))
		
		e = u'my error message'
		adapted = IStripeOperationError(e, None)
		assert_that(adapted, is_not(none()))
		assert_that(adapted.Type, is_(u'OperationError'))
		assert_that(adapted.Message, is_('my error message'))
		
		e = stripe.InvalidRequestError("++invalidtoken++", 'token id')
		adapted = IStripeOperationError(e, None)
		assert_that(adapted, verifiably_provides(IStripeOperationError))
		
