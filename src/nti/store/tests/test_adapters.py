#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import none
from hamcrest import is_not
from hamcrest import has_entry
from hamcrest import assert_that
from hamcrest import has_property

import unittest

from nti.externalization.externalization import to_external_object

from nti.store import PricingException
from nti.store.interfaces import IPricingError
from nti.store.interfaces import IPurchasableVendorInfo
from nti.store.interfaces import IPurchaseAttemptContext

from nti.store.tests import SharedConfiguringTestLayer

from nti.testing.matchers import verifiably_provides

class TestPurchasableStore(unittest.TestCase):

	layer = SharedConfiguringTestLayer

	def test_vendorinfo(self):
		d = {'a':1, 'b':2}
		vendor = IPurchasableVendorInfo(d, None)
		assert_that(vendor, is_not(none()))
		assert_that(vendor, has_entry('a', 1))
		
		ext_obj = to_external_object(vendor)
		assert_that(ext_obj, is_not(none()))

	def test_purchase_attempt_context(self):
		d = {'a':1, 'b':2}
		context = IPurchaseAttemptContext(d, None)
		assert_that(context, is_not(none()))
		assert_that(context, has_entry('b', 2))
		
		ext_obj = to_external_object(context)
		assert_that(ext_obj, is_not(none()))
		
	def test_pricing_exception(self):
		e = PricingException("foo")
		error = IPricingError(e, None)
		assert_that(error, is_not(none()))
		assert_that(error, has_property('Type', is_('PricingError')))
		assert_that(error, has_property('Message', is_('foo')))
		assert_that(error, verifiably_provides(IPricingError))
