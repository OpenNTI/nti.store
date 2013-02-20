#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import
__docformat__ = "restructuredtext en"

#disable: accessing protected members, too many methods
#pylint: disable=W0212,R0904

from nti.dataserver.users import User

from nti.externalization.externalization import to_external_object

from ... import purchase_attempt
from ... import interfaces as store_interfaces

import nti.dataserver.tests.mock_dataserver as mock_dataserver
from nti.dataserver.tests.mock_dataserver import WithMockDSTrans

from ...tests import ConfiguringTestBase

from hamcrest import (assert_that, is_, is_not, has_entry)	
	
class TestPaymentsExternal(ConfiguringTestBase):
		
	def _create_user(self, username='nt@nti.com', password='temp001'):
		ds = mock_dataserver.current_mock_ds
		usr = User.create_user( ds, username=username, password=password)
		return usr
	
	@WithMockDSTrans
	def test_stripe_payment(self):		
		user = self._create_user()		
		hist = store_interfaces.IPurchaseHistory(user, None)
		
		processor = 'stripe'
		pa = purchase_attempt.create_purchase_attempt(items='xyz', processor=processor)
		hist.add_purchase(pa)
		
		ext = to_external_object(pa)
		assert_that(ext,  has_entry('ChargeID', is_(None)))
		assert_that(ext,  has_entry('TokenID', is_(None)))
		assert_that(ext,  has_entry('OID', is_not(None)))
		
	@WithMockDSTrans
	def test_fps_payment(self):		
		user = self._create_user()		
		hist = store_interfaces.IPurchaseHistory(user, None)
		
		processor = 'fps'
		pa = purchase_attempt.create_purchase_attempt(items='xyz', processor=processor)
		hist.add_purchase(pa)
		
		ext = to_external_object(pa)
		assert_that(ext,  has_entry('TokenID', is_(None)))
		assert_that(ext,  has_entry('TransactionID', is_(None)))
		assert_that(ext,  has_entry('CallerReference', is_(None)))
		assert_that(ext,  has_entry('OID', is_not(None)))

