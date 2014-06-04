#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import none
from hamcrest import is_not
from hamcrest import has_key
from hamcrest import has_entry
from hamcrest import has_length
from hamcrest import assert_that
from hamcrest import greater_than_or_equal_to

import os
import unittest

from zope import component

from nti.contentlibrary.interfaces import IFilesystemContentPackageLibrary
from nti.contentlibrary.filesystem import DynamicFilesystemLibrary as FileLibrary

from nti.dataserver.users import User

from nti.externalization.externalization import to_external_object

from nti.store import pricing
from nti.store import priceable
from nti.store import purchasable
from nti.store import purchase_order
from nti.store import purchase_error
from nti.store import purchase_attempt
from nti.store import interfaces as store_interfaces

from nti.dataserver.tests.mock_dataserver import WithMockDSTrans

from nti.store.tests import SharedConfiguringTestLayer

class TestStoreExternal(unittest.TestCase):

	layer = SharedConfiguringTestLayer

	processor = 'stripe'

	def setUp(self):
		library = FileLibrary(os.path.join(os.path.dirname(__file__), 'library'))
		component.provideUtility(library, IFilesystemContentPackageLibrary)

	def _create_user(self, username='nt@nti.com', password='temp001'):
		usr = User.create_user(self.ds, username=username, password=password)
		return usr

	def _create_purchase_attempt(self, item=u'xyz-book', quantity=None,
								 state=store_interfaces.PA_STATE_UNKNOWN,
								 description='my purchase'):
		pi = purchase_order.create_purchase_item(item, 1)
		po = purchase_order.create_purchase_order(pi, quantity=quantity)
		pa = purchase_attempt.create_purchase_attempt(po, processor=self.processor,
													  description=description,
													  state=state)
		return pa

	@WithMockDSTrans
	def test_purchase_hist(self):
		user = self._create_user()
		hist = store_interfaces.IPurchaseHistory(user, None)

		pa = self._create_purchase_attempt(description='my charge', quantity=2)
		pa.Error = purchase_error.create_purchase_error("An error",
														type_='foo',
														code="a code")
		hist.add_purchase(pa)

		ext = to_external_object( pa )
		assert_that( ext, has_key('MimeType') )
		assert_that( ext, has_entry( 'Class', 'PurchaseAttempt') )
		assert_that( ext, has_entry( 'State', 'Unknown') )
		assert_that( ext, has_entry( 'OID', is_not(None)) )
		assert_that( ext, has_entry( 'Last Modified', is_not(none())) )
		assert_that( ext, has_entry( 'Processor', self.processor) )
		assert_that( ext, has_entry( 'StartTime', is_not(none())) )
		assert_that( ext, has_entry( 'EndTime', is_(none())) )
		assert_that( ext, has_entry( 'Description', is_('my charge')) )
		assert_that( ext, has_entry( 'InvitationCode', is_not(none())) )
		assert_that( ext, has_entry( 'Error', has_entry('Message', pa.Error.Message) ) )

		# check order
		assert_that(ext, has_key('Order'))
		order = ext['Order']
		assert_that(order, has_entry('Quantity', is_(2)))
		assert_that(order, has_entry('Items', has_length(1)))
		items = order['Items']
		assert_that(items[0], has_entry('NTIID', 'xyz-book'))
		assert_that(items[0], has_entry('Quantity', 2))


	@WithMockDSTrans
	def test_purchase_order(self):
		pi_1 = purchase_order.create_purchase_item("ichigo", 1)
		pi_2 = purchase_order.create_purchase_item("aizen", 2)
		po = purchase_order.create_purchase_order((pi_1, pi_2))
		ext = to_external_object(po)
		assert_that(ext, has_entry('Items', has_length(2)))
		assert_that(ext, has_entry('Quantity', is_(none())))
		items = ext['Items']
		assert_that(items[0], has_entry('NTIID', 'ichigo'))
		assert_that(items[0], has_entry('Quantity', 1))
		assert_that(items[1], has_entry('NTIID', 'aizen'))
		assert_that(items[1], has_entry('Quantity', 2))

	@WithMockDSTrans
	def test_purchasable(self):
		ps = purchasable.get_purchasable('iid_3')
		ext = to_external_object(ps)

		assert_that(ext, has_key('MimeType'))
		assert_that(ext, has_entry('NTIID', u'iid_3'))
		assert_that(ext, has_entry('Class', u'Purchasable'))
		assert_that(ext, has_entry('Amount', 90))
		assert_that(ext, has_entry('Currency', u'USD'))
		assert_that(ext, has_entry('BulkPurchase', False))
		assert_that(ext, has_entry('Discountable', True))
		assert_that(ext, has_entry('Provider', u'PRMIA'))
		assert_that(ext, has_entry('Title', u'Risk Course'))
		assert_that(ext, has_entry('Author', u'Alan Laubsch'))
		assert_that(ext, has_entry('Icon', u'http://prmia.org/'))
		assert_that(ext, has_entry('Description', u'Intro to Risk'))

	def test_priceable(self):
		pp = priceable.create_priceable(u'iid_3', 1)
		ext = to_external_object(pp)
		assert_that(ext, has_key('MimeType'))
		assert_that(ext, has_entry('NTIID', u'iid_3'))
		assert_that(ext, has_entry('Quantity', 1))
		assert_that(ext, has_entry('Class', u'Priceable'))

	def test_priced_item(self):
		pp = pricing.create_priced_item(ntiid=u'iid_3', purchase_price=100, purchase_fee=2)
		ext = to_external_object(pp)
		assert_that(ext, has_key('MimeType'))
		assert_that(ext, is_not(has_key('PurchaseFee')))
		assert_that(ext, is_not(has_key('NonDiscountedPrice')))
		assert_that(ext, has_entry('Provider', u'PRMIA'))
		assert_that(ext, has_entry('PurchasePrice', 100))
		assert_that(ext, has_entry('Class', u'PricedItem'))

		pp = pricing.create_priced_item(ntiid=u'iid_3', purchase_price=200,
										purchase_fee=30, non_discounted_price=220,
										quantity=10)
		ext = to_external_object(pp)
		assert_that(ext, is_not(has_key('PurchaseFee')))
		assert_that(ext, has_entry('NonDiscountedPrice', 220))
		assert_that(ext, has_entry('PurchasePrice', 200))
		assert_that(ext, has_entry('Quantity', 10))

	def test_course(self):
		cs = purchasable.get_purchasable('tag:nextthought.com,2011-10:OU-course-CLC3403LawAndJustice')
		ext = to_external_object(cs)
		assert_that(ext, has_entry('Title', u'CLC 3403 Law and Justice'))
		assert_that(ext, has_entry('Description', has_length(greater_than_or_equal_to(140))))
		assert_that(ext, has_entry('Author', u'Kyle Harper'))
		assert_that(ext, has_entry('Amount', is_(none())))
		assert_that(ext, has_entry('Currency', is_(none())))
		assert_that(ext, has_entry('Provider', is_(none())))
		assert_that(ext, has_entry('Featured', is_(True)))
		assert_that(ext, has_entry('Icon', is_("http://www.ou.edu/icon.gif")))
		assert_that(ext, has_entry('Thumbnail', is_("http://www.ou.edu/thumbnail.gif")))
		assert_that(ext, has_entry('ID', is_('tag:nextthought.com,2011-10:OU-course-CLC3403LawAndJustice')))
		assert_that(ext, has_entry('MimeType', u'application/vnd.nextthought.course'))
		assert_that(ext, has_entry('Items', is_([u'tag:nextthought.com,2011-10:OU-HTML-CLC3403_LawAndJustice.clc_3403_law_and_justice'])))
		assert_that(ext, has_entry('StartDate', is_('2013-05-11')))
