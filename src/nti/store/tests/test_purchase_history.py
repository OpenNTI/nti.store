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

import zope.intid
from zope import component

import time
import unittest

from zope.event import notify

from nti.dataserver.users import User
from nti.externalization.oids import to_external_ntiid_oid

from nti.store.purchase_order import create_purchase_item
from nti.store.purchase_order import create_purchase_order
from nti.store.purchase_history import get_purchase_attempt
from nti.store.purchase_history import get_pending_purchases
from nti.store.purchase_attempt import create_purchase_attempt
from nti.store.purchase_history import register_purchase_attempt

from nti.store.interfaces import PA_STATE_STARTED
from nti.store.interfaces import PA_STATE_SUCCESS
from nti.store.interfaces import PA_STATE_UNKNOWN
from nti.store.interfaces import PA_STATE_REFUNDED

from nti.store.interfaces import IPurchaseHistory
from nti.store.interfaces import PurchaseAttemptRefunded

from nti.store.store import get_purchase_history
from nti.store.store import delete_purchase_history

from nti.dataserver.tests import mock_dataserver
from nti.dataserver.tests.mock_dataserver import WithMockDSTrans

from nti.store.tests import SharedConfiguringTestLayer

class TestPurchaseHistory(unittest.TestCase):

	layer = SharedConfiguringTestLayer

	processor = 'stripe'

	def _create_user(self, username='nt@nti.com', password='temp001'):
		usr = User.create_user(self.ds, username=username, password=password)
		return usr

	def _create_purchase_attempt(self, item=u'xyz-book', quantity=None, state=None):
		state = state or PA_STATE_UNKNOWN
		pi = create_purchase_item(item, 1)
		assert_that(hash(pi), is_(not_none()))
		po = create_purchase_order(pi, quantity=quantity)
		assert_that(hash(po), is_(not_none()))
		pa = create_purchase_attempt(po, processor=self.processor, state=state)
		assert_that(hash(pa), is_(not_none()))
		return pa

	@WithMockDSTrans
	def test_purchase_simple_history(self):
		user = self._create_user()
		hist = IPurchaseHistory(user, None)
		assert_that(hist, is_(not_none()))
		assert_that(hist, has_property('__parent__', is_(user)))

		hist = get_purchase_history(user, safe=False)
		assert_that(hist, is_(not_none()))
		assert_that(hist, has_property('__parent__', is_(user)))
		
		pa_1 = self._create_purchase_attempt()
		hist.add_purchase(pa_1)
		assert_that(hist, has_length(1))

		oid = to_external_ntiid_oid(pa_1)
		assert_that(pa_1, has_property('id', is_(oid)))
		assert_that(pa_1, has_property('__name__', is_(pa_1.id)))
		assert_that(pa_1, has_property('__parent__', is_(hist)))
		
		pa_2 = self._create_purchase_attempt('zky')
		hist.add_purchase(pa_2)
		assert_that(hist, has_length(2))

		assert_that(list(hist.values()), has_length(2))

		t = (pa_1, pa_2)
		ck = all([c in t for c in hist])
		assert_that(ck, is_(True))

		oid = to_external_ntiid_oid(pa_2)
		assert_that(hist.get_purchase(oid), is_(pa_2))

		hist.remove_purchase(pa_2)
		assert_that(hist, has_length(1))
		
		assert_that(delete_purchase_history(user), is_(True))

	@WithMockDSTrans
	def test_purchase_remove(self):
		user = self._create_user()
		hist = IPurchaseHistory(user)
		pa_1 = self._create_purchase_attempt()
		hist.add_purchase(pa_1)
		assert_that(hist, has_length(1))

		intids = component.getUtility(zope.intid.IIntIds)
		iid = intids.queryId(pa_1)
		assert_that(iid, is_(not_none()))
		queried = intids.queryObject(iid)
		assert_that(queried, is_(pa_1))
		
		r = hist.remove_purchase(pa_1)
		assert_that(r, is_(True))
		assert_that(hist, has_length(0))
		
		old_iid = intids.queryId(pa_1)
		assert_that(old_iid, is_(none()))
		queried = intids.queryObject(iid)
		assert_that(queried, is_(none()))
		
		# chec after removal
		hist._v_check()

	@WithMockDSTrans
	def test_purchase_has_history_by_item(self):
		user = self._create_user()
		hist = IPurchaseHistory(user)

		pa_1 = self._create_purchase_attempt(quantity=5)
		hist.add_purchase(pa_1)
		assert_that(hist, has_length(1))

		v = hist.has_history_by_item('xyz-book')
		assert_that(v, is_(True))

		hist.remove_purchase(pa_1)
		v = hist.has_history_by_item('xyz-book')
		assert_that(v, is_(False))

		pa_1 = self._create_purchase_attempt()
		hist.add_purchase(pa_1)
		v = hist.has_history_by_item('xyz-book')
		assert_that(v, is_(True))

		pa_1 = self._create_purchase_attempt(quantity=10)
		hist.add_purchase(pa_1)
		v = hist.has_history_by_item('xyz-book')
		assert_that(v, is_(True))

	@WithMockDSTrans
	def test_pending_purchase(self):
		user = self._create_user()
		hist = IPurchaseHistory(user, None)

		item = u'xyz-book'
		pending = self._create_purchase_attempt(item, state=PA_STATE_STARTED)
		hist.add_purchase(pending)

		purchases = get_pending_purchases(user, item)
		assert_that(purchases, is_(not_none()))
		assert_that(purchases, has_length(1))
		assert_that(purchases[0], is_(pending))

	@WithMockDSTrans
	def test_missing_purchase(self):
		user = self._create_user()
		purchase_id = u'tag:nextthought.com,2011-10:system-OID-0x06cdce28af3dc253:0000000073:XVq3tFG7T82'
		pa = get_purchase_attempt(purchase_id, user)
		assert_that(pa, is_(none()))

	@WithMockDSTrans
	def test_refund(self):
		user = self._create_user()
		book = 'tag:nextthought.com,2011-10:MN-HTML-MiladyCosmetology.cosmetology'
		purchase = self._create_purchase_attempt(book, state=PA_STATE_SUCCESS)
		register_purchase_attempt(purchase, user)
		notify(PurchaseAttemptRefunded(purchase))
		assert_that(purchase.State, is_(PA_STATE_REFUNDED))

	@WithMockDSTrans
	def test_refund_invitation_attempt(self):
		user_1 = self._create_user()
		user_2 = self._create_user(username='nt2@nti.com',)
		book = 'tag:nextthought.com,2011-10:MN-HTML-MiladyCosmetology.cosmetology'

		pa_1 = self._create_purchase_attempt(book, quantity=5, state=PA_STATE_SUCCESS)
		register_purchase_attempt(pa_1, user_1)

		pa_2 = self._create_purchase_attempt(book, state=PA_STATE_SUCCESS)
		register_purchase_attempt(pa_2, user_2)

		pa_1.register(user_2, pa_2.id)

		notify(PurchaseAttemptRefunded(pa_1))
		assert_that(pa_1.State, is_(PA_STATE_REFUNDED))
		assert_that(pa_2.State, is_(PA_STATE_REFUNDED))

	@mock_dataserver.WithMockDS
	def test_purchase_history_check(self):
		now = time.time()
		t50 = 0
		with mock_dataserver.mock_db_trans(self.ds):
			user = self._create_user()
			username = user.username

		def _get_hist():
			user = User.get_user(username)
			hist = IPurchaseHistory(user)
			return hist

		for i in range(0, 100):
			item = unicode(i)
			if i == 50:
				t50 = time.time()
			with mock_dataserver.mock_db_trans(self.ds):
				hist = _get_hist()
				pa = self._create_purchase_attempt(item)
				hist.add_purchase(pa)
				hist._v_check()

		with mock_dataserver.mock_db_trans(self.ds):
			hist = _get_hist()
			hist._v_check()

			count = 0
			for _ in hist:
				count += 1
			assert_that(count, is_(100))
			assert_that(hist, has_length(100))

			lst = list(hist.get_purchase_history())
			assert_that(lst, has_length(100))

			lst = list(hist.get_purchase_history(end_time=now))
			assert_that(lst, has_length(0))

			lst = list(hist.get_purchase_history(start_time=now))
			assert_that(lst, has_length(100))

			lst = list(hist.get_purchase_history(start_time=now, end_time=t50))
			assert_that(lst, has_length(50))

			lst = list(hist.get_purchase_history(start_time=now, end_time=t50))
			assert_that(lst, has_length(50))

			lst = list(hist.get_purchase_history_by_item(u'10'))
			assert_that(lst, has_length(1))
			
			assert_that(hist.clear(), is_(100))
			assert_that(hist, has_length(0))
			hist._v_check()
