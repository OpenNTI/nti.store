#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import none
from hamcrest import is_in
from hamcrest import is_not
from hamcrest import has_length
from hamcrest import assert_that

import unittest

from nti.dataserver.users import User

from nti.ntiids.ntiids import find_object_with_ntiid

from nti.store.purchasable import get_purchasable
from nti.store.purchasable import expand_purchase_item_ids

from nti.store.purchase_order import create_purchase_item
from nti.store.purchase_order import create_purchase_order
from nti.store.purchase_attempt import create_purchase_attempt

from nti.store.tests import SharedConfiguringTestLayer

class TestPurchasable(unittest.TestCase):

	layer = SharedConfiguringTestLayer

	processor = 'stripe'

	def _create_user(self, username='nt@nti.com', password='temp001'):
		usr = User.create_user(self.ds, username=username, password=password)
		return usr

	def test_ntiids(self):
		assert_that(find_object_with_ntiid('tag:nextthought.com,2011-10:NextThought-purchasable-HelpCenter'), 
					is_not(none()))
		
	def test_zmcl(self):
		assert_that(get_purchasable('iid_0'), is_not(none()))

		ps = get_purchasable('iid_3')
		assert_that(ps.NTIID, is_("iid_3"))
		assert_that(ps.Title, is_("Risk Course"))
		assert_that(ps.Description, is_("Intro to Risk"))
		assert_that(ps.Provider, is_("PRMIA"))
		assert_that(ps.Amount, is_(90))
		assert_that(ps.Currency, is_("USD"))
		assert_that(ps.Discountable, is_(True))
		assert_that(ps.BulkPurchase, is_(False))
		assert_that(ps.Items, has_length(2))
		assert_that(ps.License, "1 Year License")

	def _create_purchase_attempt(self, item=u'iid_3', quantity=None, state=None):
		pi = create_purchase_item(item, 1)
		po = create_purchase_order(pi, quantity=quantity)
		pa = create_purchase_attempt(po, processor=self.processor, state=state)
		return pa

	def test_expand_purchase_item_ids(self):
		items = expand_purchase_item_ids("iid_3")
		assert_that(items, has_length(2))
		assert_that('var-risk', is_in(items))
		assert_that('volatility', is_in(items))
