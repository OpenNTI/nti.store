#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import none
from hamcrest import is_not
from hamcrest import has_length
from hamcrest import assert_that

import uuid
import stripe
import unittest

from zope import component

from nti.store import interfaces as store_interfaces
from ..stripe_purchase import create_stripe_priceable

from . import find_test
from . import SharedConfiguringTestLayer

class UtilsTestLayer(SharedConfiguringTestLayer):

	@classmethod
	def setUp(cls):
		super(UtilsTestLayer, cls).setUp()
		code = str(uuid.uuid4())
		cls.api_key = stripe.api_key
		stripe.api_key = u'sk_test_3K9VJFyfj0oGIMi7Aeg3HNBp'
		cls.coupon = stripe.Coupon.create(percent_off=25, duration='once', id=code)
		
	@classmethod
	def testSetUp(cls, test=None):
		super(UtilsTestLayer, cls).testSetUp(test)
		cls.test = test or find_test()
		cls.test.coupon = cls.coupon

	@classmethod
	def tearDown(cls):
		super(UtilsTestLayer, cls).tearDown()
		cls.test.coupon.delete()
		stripe.api_key = cls.api_key

class TestUtils(unittest.TestCase):

	layer = UtilsTestLayer

	def test_price(self):
		pricer = component.getUtility(store_interfaces.IPurchasablePricer, name="stripe")
		p = create_stripe_priceable(u"bleach", 5, self.coupon.id)
		priced = pricer.price(p)
		assert_that(priced, is_not(none()))
		assert_that(priced.NTIID, is_(u'bleach'))
		assert_that(priced.PurchaseFee, is_(0))
		assert_that(priced.PurchasePrice, is_(750))
		assert_that(priced.NonDiscountedPrice, is_(1000))
		assert_that(priced.Quantity, is_(5))

	def test_evaluate(self):
		pricer = component.getUtility(store_interfaces.IPurchasablePricer, name="stripe")
		p0 = create_stripe_priceable(u"bleach", 5, self.coupon.id)
		p1 = create_stripe_priceable(u"xyz-book", 1)
		result = pricer.evaluate((p0, p1))
		assert_that(result, is_not(none()))
		assert_that(result.Items, has_length(2))
		assert_that(result.TotalPurchaseFee, is_(0))
		assert_that(result.TotalPurchasePrice, is_(850))
		assert_that(result.TotalNonDiscountedPrice, is_(1100))

	def test_evaluate_fee(self):
		pricer = component.getUtility(store_interfaces.IPurchasablePricer, name="stripe")
		p0 = create_stripe_priceable(u"gotye", 10, self.coupon.id)
		p1 = create_stripe_priceable(u"xyz-book", 3)
		result = pricer.evaluate((p0, p1))
		assert_that(result, is_not(none()))
		assert_that(result.Items, has_length(2))
		assert_that(result.TotalPurchaseFee, is_(150))
		assert_that(result.TotalPurchasePrice, is_(1800))
		assert_that(result.TotalNonDiscountedPrice, is_(2300))
