#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import has_length
from hamcrest import assert_that
from hamcrest import has_property

import unittest

from zope import interface

from nti.dataserver.users import User
from nti.externalization.oids import to_external_ntiid_oid

from nti.store.purchase_order import create_purchase_item
from nti.store.purchase_order import create_purchase_order
from nti.store.purchase_attempt import create_purchase_attempt

from nti.store.interfaces import PA_STATE_STARTED
from nti.store.interfaces import IPurchaseHistory
from nti.store.purchase_history import get_purchase_attempt
from nti.store.generations.evolve2 import update_user_purchase_data

from nti.common.deprecated import hiding_warnings
with hiding_warnings():
	from nti.store.interfaces import IEnrollmentAttempt
	
from nti.dataserver.tests import mock_dataserver

from nti.store.tests import SharedConfiguringTestLayer

class TestEvolve2(unittest.TestCase):

	layer = SharedConfiguringTestLayer

	processor = 'stripe'

	def _create_user(self, username='nt@nti.com', password='temp001'):
		usr = User.create_user(self.ds, username=username, password=password)
		return usr

	def _create_purchase_attempt(self, item=u'xyz-book', quantity=None, state=None):
		state = state or PA_STATE_STARTED
		pi = create_purchase_item(item, 1)
		po = create_purchase_order(pi, quantity=quantity)
		pa = create_purchase_attempt(po, processor=self.processor, state=state)
		return pa

	@mock_dataserver.WithMockDS
	def test_evolve(self):
		
		with mock_dataserver.mock_db_trans(self.ds):
			user = self._create_user()
			hist = IPurchaseHistory(user)

			pa = self._create_purchase_attempt()
			hist.add_purchase(pa)
			pa.id = 'foo' # change name
			oid = to_external_ntiid_oid(pa)
			
			fake = self._create_purchase_attempt()
			interface.alsoProvides(fake, IEnrollmentAttempt)
			hist.add_purchase(fake)
			
			assert_that(hist, has_length(2))
			
		with mock_dataserver.mock_db_trans(self.ds):
			user = User.get_user('nt@nti.com')
			hist = IPurchaseHistory(user)
			assert_that(hist, has_length(2))
			
			pa = get_purchase_attempt(oid)
			assert_that(pa, has_property('id', is_('foo')))
			# evolve
			uc, rc = update_user_purchase_data(user)
			assert_that(uc, is_(1))
			assert_that(rc, is_(1))
			assert_that(pa, has_property('id', is_(oid)))
			
			assert_that(hist, has_length(1))
