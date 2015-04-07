#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import none
from hamcrest import not_none
from hamcrest import has_length
from hamcrest import assert_that
from hamcrest import has_property

import unittest

from nti.store.purchase_order import create_purchase_item
from nti.store.purchase_order import create_purchase_order

from nti.store.tests import SharedConfiguringTestLayer

class TestPurchaseOrder(unittest.TestCase):

	layer = SharedConfiguringTestLayer

	processor = 'stripe'

	def test_purchase_order(self):
		
		items = []
		for item in (u'ichigo', u'aizen'):
			items.append(create_purchase_item(item, 1))
				
		order = create_purchase_order(items)
		assert_that(hash(order), is_(not_none()))
		
		assert_that(order, has_length(2))
		assert_that(order, has_property('Quantity', is_(none())))
		assert_that(order, has_property('NTIIDs', is_((u'ichigo', u'aizen'))))
		
		iterable = list(order)
		assert_that(iterable, has_length(2))
		
		for idx, name in enumerate((u'ichigo', u'aizen')):
			item = order[idx]
			assert_that(item, has_property('NTIID', is_(name)))
			assert_that(item, has_property('Quantity', is_(1)))
		
		order = order.copy()
		assert_that(order, has_length(2))
		assert_that(order, has_property('NTIIDs', is_((u'ichigo', u'aizen'))))
		
		order = order.copy(None)
		assert_that(order, has_length(2))
		assert_that(order, has_property('NTIIDs', is_((u'ichigo', u'aizen'))))
		
		order = order.copy('aizen')
		assert_that(order, has_length(1))
		assert_that(order, has_property('NTIIDs', is_((u'aizen',))))
		