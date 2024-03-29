#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import none
from hamcrest import is_not
from hamcrest import has_length
from hamcrest import assert_that

import unittest

from zope import component

from nti.store import priceable

from nti.store.interfaces import IPurchasablePricer

from nti.store.tests import SharedConfiguringTestLayer


class TestPurchasableStore(unittest.TestCase):

    layer = SharedConfiguringTestLayer

    def test_price(self):
        pricer = component.getUtility(IPurchasablePricer)
        p = priceable.create_priceable(u"iid_0", 10)
        priced = pricer.price(p)
        assert_that(priced, is_not(none()))
        assert_that(priced.NTIID, is_('iid_0'))
        assert_that(priced.PurchaseFee, is_(200))
        assert_that(priced.PurchasePrice, is_(1000))
        assert_that(priced.Quantity, is_(10))

        p = priceable.create_priceable(u"iid_2", 2)
        priced = pricer.price(p)
        assert_that(priced, is_not(none()))
        assert_that(priced.NTIID, is_('iid_2'))
        assert_that(priced.PurchaseFee, is_(36.42))
        assert_that(priced.PurchasePrice, is_(181.66))
        assert_that(priced.Quantity, is_(2))

    def test_evaluate(self):
        pricer = component.getUtility(IPurchasablePricer)
        p0 = priceable.create_priceable(u"iid_0", 5)
        p1 = priceable.create_priceable(u"iid_1", 7)
        result = pricer.evaluate((p0, p1))
        assert_that(result, is_not(none()))
        assert_that(result.Items, has_length(2))
        assert_that(result.TotalPurchaseFee, is_(100))
        assert_that(result.TotalPurchasePrice, is_(1340))
