#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import is_not
from hamcrest import has_entry
from hamcrest import assert_that

import unittest

from nti.dataserver.users import User

from nti.externalization.externalization import to_external_object

from nti.store import purchase_order
from nti.store import purchase_attempt
from nti.store import interfaces as store_interfaces

import nti.dataserver.tests.mock_dataserver as mock_dataserver
from nti.dataserver.tests.mock_dataserver import WithMockDSTrans

from nti.store.tests import SharedConfiguringTestLayer

class TestPaymentsExternal(unittest.TestCase):

	layer = SharedConfiguringTestLayer

	def _create_user(self, username='nt@nti.com', password='temp001'):
		ds = mock_dataserver.current_mock_ds
		usr = User.create_user(ds, username=username, password=password)
		return usr


	def _create_purchase_attempt(self, item=u'xyz-book', processor=None,
								 state=store_interfaces.PA_STATE_UNKNOWN,
								 description=None):
		pi = purchase_order.create_purchase_item(item, 1)
		po = purchase_order.create_purchase_order(pi)
		pa = purchase_attempt.create_purchase_attempt(po, processor=processor,
													  description=description,
													  state=state)
		return pa
	@WithMockDSTrans
	def test_stripe_purchase_attempt(self):
		user = self._create_user()
		hist = store_interfaces.IPurchaseHistory(user, None)

		processor = 'stripe'
		pa = self._create_purchase_attempt(processor=processor)
		hist.add_purchase(pa)

		ext = to_external_object(pa)
		assert_that(ext, has_entry('ChargeID', is_(None)))
		assert_that(ext, has_entry('TokenID', is_(None)))
		assert_that(ext, has_entry('OID', is_not(None)))

