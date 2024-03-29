#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import assert_that

import time
import unittest

from nti.store.payments.stripe.processor.coupon import CouponProcessor

from nti.store.payments.stripe.processor.tests import StripeProcessorTestLayer


class TestCouponProcessor(unittest.TestCase):

    layer = StripeProcessorTestLayer

    def setUp(self):
        super(TestCouponProcessor, self).setUp()
        self.manager = CouponProcessor()

    def test_validate_coupon(self):

        class Coupon(object):
            duration = u'forever'
            redeem_by = None
            times_redeemed = 0
            created = time.time()
            max_redemptions = None
            duration_in_months = None

        c = Coupon()
        c.duration = u'forever'
        assert_that(self.manager.validate_coupon(c), is_(True))

        c.duration = u'once'
        assert_that(self.manager.validate_coupon(c), is_(True))
        c.redeem_by = time.time() + 100000
        assert_that(self.manager.validate_coupon(c), is_(True))
        c.redeem_by = time.time() - 100000
        assert_that(self.manager.validate_coupon(c), is_(False))

        c.duration = u'repeating'
        assert_that(self.manager.validate_coupon(c), is_(False))
        c.redeem_by = time.time() + 100000
        assert_that(self.manager.validate_coupon(c), is_(True))
        c.redeem_by = None

        c.max_redemptions = 0
        assert_that(self.manager.validate_coupon(c), is_(False))
        c.max_redemptions = 1
        assert_that(self.manager.validate_coupon(c), is_(True))
        c.max_redemptions = None

        c.created = c.created - 10000000
        c.duration_in_months = 5
        assert_that(self.manager.validate_coupon(c), is_(True))

        c.duration_in_months = 2
        assert_that(self.manager.validate_coupon(c), is_(False))

    def test_apply_coupon(self):
        amount = 1000

        class Coupon(object):
            amount_off = None
            percent_off = None

        c = Coupon()
        c.percent_off = 0.10
        amt = self.manager.apply_coupon(amount, c)
        assert_that(amt, is_(900))

        c = Coupon()
        c.percent_off = 20.0
        amt = self.manager.apply_coupon(amount, c)
        assert_that(amt, is_(800))

        c = Coupon()
        c.amount_off = 2000
        amt = self.manager.apply_coupon(amount, c)
        assert_that(amt, is_(980))
