#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division
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

from nti.store.interfaces import IPurchaseHistory

from nti.store.purchase_attempt import create_purchase_attempt

from nti.store.purchase_order import create_purchase_item
from nti.store.purchase_order import create_purchase_order

from nti.dataserver.tests import mock_dataserver

from nti.store.tests import SharedConfiguringTestLayer


class TestPaymentsExternal(unittest.TestCase):

    layer = SharedConfiguringTestLayer

    def _create_user(self, username=u'nt@nti.com', password=u'temp001'):
        ds = mock_dataserver.current_mock_ds
        usr = User.create_user(ds, username=username, password=password)
        return usr

    def _create_purchase_attempt(self, item=u'xyz-book', processor=None,
                                 state=None, description=None):
        pi = create_purchase_item(item, 1)
        po = create_purchase_order(pi)
        pa = create_purchase_attempt(po, processor=processor,
                                     description=description,
                                     state=state)
        return pa

    @mock_dataserver.WithMockDSTrans
    def test_stripe_purchase_attempt(self):
        user = self._create_user()
        hist = IPurchaseHistory(user, None)

        processor = 'stripe'
        pa = self._create_purchase_attempt(processor=processor)
        hist.add_purchase(pa)

        ext = to_external_object(pa)
        assert_that(ext, has_entry('ChargeID', is_(None)))
        assert_that(ext, has_entry('TokenID', is_(None)))
        assert_that(ext, has_entry('OID', is_not(None)))
