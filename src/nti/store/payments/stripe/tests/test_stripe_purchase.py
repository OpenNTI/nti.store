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
from hamcrest import has_length
from hamcrest import assert_that
from hamcrest import has_property

import unittest

from nti.externalization.internalization import find_factory_for 
from nti.externalization.externalization import to_external_object
from nti.externalization.internalization import update_from_external_object 

from nti.store.payments.stripe import stripe_purchase

from nti.dataserver.tests.mock_dataserver import WithMockDSTrans

from nti.store.tests import SharedConfiguringTestLayer

class TestStripePurchase(unittest.TestCase):

	layer = SharedConfiguringTestLayer

	book_id = 'xyz-book'

	def _create_purchase_order(self, item, quantity=None, coupon=None):
		pi = stripe_purchase.create_stripe_purchase_item(item, 1)
		po = stripe_purchase.create_stripe_purchase_order(pi,
														  quantity=quantity,
														  coupon=coupon)
		return po

	@WithMockDSTrans
	def test_copy_purchase_order(self):
		po = self._create_purchase_order(self.book_id, quantity=2,
										 coupon='mycoupon')
		cp = po.copy()
		assert_that(cp, is_not(none()))
		assert_that(id(po), is_not(id(cp)))
		# check items
		assert_that(cp.Items, has_length(1))
		assert_that(cp.Items[0].NTIID, is_(self.book_id))
		assert_that(cp.Items[0].Quantity, is_(2))
		# check order
		assert_that(cp.Coupon, is_('mycoupon'))
		assert_that(cp.Quantity, is_(2))
		
	@WithMockDSTrans
	def test_externalize(self):
		po = self._create_purchase_order(self.book_id, quantity=2,
										 coupon='mycoupon')
		ext_obj = to_external_object(po)
		assert_that(ext_obj, has_entry('Class', 'StripePurchaseOrder'))
		assert_that(ext_obj, has_entry('MimeType', 'application/vnd.nextthought.store.stripepurchaseorder'))

		factory = find_factory_for(ext_obj)
		assert_that(factory, is_not(none()))
		
		new_po = factory()
		update_from_external_object(new_po, ext_obj)
		
		assert_that(new_po, has_property('Coupon', 'mycoupon'))
		assert_that(new_po.Items, has_length(1))