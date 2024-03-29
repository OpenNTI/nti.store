#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import is_not
from hamcrest import assert_that
from hamcrest import has_property

import unittest

from zope import component

from zope.intid.interfaces import IIntIds

from nti.externalization import integer_strings

from nti.store import purchase_history
from nti.store import interfaces as store_interfaces

from nti.store.payments.stripe.processor.refund import RefundProcessor
from nti.store.payments.stripe.processor.purchase import PurchaseProcessor

import nti.dataserver.tests.mock_dataserver as mock_dataserver

from nti.dataserver.tests.mock_dataserver import WithMockDS

from nti.store.payments.stripe.processor.tests import create_purchase
from nti.store.payments.stripe.processor.tests import TEST_WITH_STRIPE
from nti.store.payments.stripe.processor.tests import StripeProcessorTestLayer

class TestRefundProcessor(unittest.TestCase):

	layer = StripeProcessorTestLayer

	def setUp(self):
		super(TestRefundProcessor, self).setUp()
		self.manager = RefundProcessor()
		self.purchase = PurchaseProcessor()

	create_purchase = create_purchase

	@unittest.skipUnless(TEST_WITH_STRIPE, '')
	@WithMockDS
	def test_refund_purchase(self):
		ds = self.ds
		username, purchase_id, _, _ = self.create_purchase(manager=self.purchase)

		with mock_dataserver.mock_db_trans(ds):
			pa = purchase_history.get_purchase_attempt(purchase_id, username)
			assert_that(pa.State, is_(store_interfaces.PA_STATE_SUCCESS))

			# start refund
			zope_iids = component.getUtility(IIntIds)
			uid = zope_iids.getId(pa)
			trx_id = integer_strings.to_external_string(uid)
			charge = self.manager.refund_purchase(trx_id)
			assert_that(charge, is_not(None))
			assert_that(charge, has_property('refunded', is_(True)))

			pa = purchase_history.get_purchase_attempt(purchase_id, username)
			assert_that(pa.State, is_(store_interfaces.PA_STATE_REFUNDED))

	@unittest.skipUnless(TEST_WITH_STRIPE, '')
	@WithMockDS
	def test_refund_purchase_50(self):
		ds = self.ds
		username, purchase_id, _, _ = self.create_purchase(manager=self.purchase)

		with mock_dataserver.mock_db_trans(ds):
			pa = purchase_history.get_purchase_attempt(purchase_id, username)
			assert_that(pa.State, is_(store_interfaces.PA_STATE_SUCCESS))

			# start refund
			zope_iids = component.getUtility(IIntIds)
			uid = zope_iids.getId(pa)
			trx_id = integer_strings.to_external_string(uid)
			charge = self.manager.refund_purchase(trx_id, amount=50)
			assert_that(charge, is_not(None))
			assert_that(charge, has_property('refunded', is_(False)))
			assert_that(charge, has_property('amount_refunded', is_(5000)))

			pa = purchase_history.get_purchase_attempt(purchase_id, username)
			assert_that(pa.State, is_(store_interfaces.PA_STATE_REFUNDED))
