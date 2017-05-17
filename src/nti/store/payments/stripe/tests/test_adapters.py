#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import none
from hamcrest import is_in
from hamcrest import is_not
from hamcrest import assert_that
from hamcrest import has_property

from nti.testing.matchers import validly_provides
from nti.testing.matchers import verifiably_provides

import unittest

import stripe

from nti.dataserver.users import User

from nti.store.payments.stripe import StripeException

from nti.store.payments.stripe.interfaces import IStripeCustomer
from nti.store.payments.stripe.interfaces import IStripePurchaseError
from nti.store.payments.stripe.interfaces import IStripeOperationError
from nti.store.payments.stripe.interfaces import IStripePurchaseAttempt

from nti.store.purchase_order import create_purchase_item
from nti.store.purchase_order import create_purchase_order

from nti.store.purchase_attempt import create_purchase_attempt

from nti.dataserver.tests import mock_dataserver

from nti.store.tests import SharedConfiguringTestLayer


class TestStripeAdapters(unittest.TestCase):

    layer = SharedConfiguringTestLayer

    processor = 'stripe'

    def _create_user(self, username=u'nt@nti.com', password=u'temp001'):
        ds = mock_dataserver.current_mock_ds
        usr = User.create_user(ds, username=username, password=password)
        return usr

    @mock_dataserver.WithMockDSTrans
    def test_stripe_customer_adapter(self):
        user = self._create_user()
        adapted = IStripeCustomer(user)
        assert_that(adapted, is_not(none()))
        assert_that(adapted, has_property('CustomerID', is_(none())))

        adapted.Charges.add(u'ch_id')
        assert_that('ch_id', is_in(adapted))

        adapted.customer_id = u'xyz'
        assert_that(adapted, has_property('CustomerID', is_(is_('xyz'))))

    def _create_purchase_attempt(self, item=u'xyz-book', quantity=None, 
								 state=None, description=u'my purchase'):
        item = create_purchase_item(item, 1)
        order = create_purchase_order(item, quantity=quantity)
        result = create_purchase_attempt(order, 
										 processor=self.processor,
                                         description=description,
                                         state=state)
        return result

    @mock_dataserver.WithMockDSTrans
    def test_stripe_purchase_adapter(self):
        pa = self._create_purchase_attempt()
        adapted = IStripePurchaseAttempt(pa)
        adapted.charge_id = u'charge_id'
        adapted.token_id = u'token_id'
        assert_that(adapted.purchase, is_(pa))
        assert_that(adapted.charge_id, is_('charge_id'))
        assert_that(adapted.token_id, is_('token_id'))

    def test_exception_adapter(self):
        e = StripeException(u'my exception')
        adapted = IStripePurchaseError(e, None)
        assert_that(adapted, is_not(none()))
        assert_that(adapted.Type, is_('PurchaseError'))
        assert_that(adapted.Message, is_('my exception'))

    def test_stripe_error_adapters(self):
        e = stripe.CardError(u'my error', u'my param', u'my code')
        adapted = IStripeOperationError(e, None)
        assert_that(adapted, is_not(none()))
        assert_that(adapted.Type, is_('CardError'))
        assert_that(adapted.Message, is_('my error'))
        assert_that(adapted.Param, is_('my param'))
        assert_that(adapted.Code, is_('my code'))
        assert_that(adapted, validly_provides(IStripeOperationError))
        assert_that(adapted, verifiably_provides(IStripeOperationError))

        e = u'my error message'
        adapted = IStripeOperationError(e, None)
        assert_that(adapted, is_not(none()))
        assert_that(adapted.Type, is_('OperationError'))
        assert_that(adapted.Message, is_('my error message'))

        e = stripe.InvalidRequestError(u"++invalidtoken++", u'token id')
        adapted = IStripeOperationError(e, None)
        assert_that(adapted, validly_provides(IStripeOperationError))
        assert_that(adapted, verifiably_provides(IStripeOperationError))
