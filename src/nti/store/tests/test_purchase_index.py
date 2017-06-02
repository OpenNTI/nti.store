#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import none
from hamcrest import is_not
from hamcrest import has_length
from hamcrest import assert_that

import unittest

from nti.store.purchase_index import StoreCatalog
from nti.store.purchase_index import get_purchase_catalog

from nti.dataserver.tests.mock_dataserver import WithMockDSTrans

from nti.store.tests import SharedConfiguringTestLayer


class TestPurchaseIndex(unittest.TestCase):

    layer = SharedConfiguringTestLayer

    @WithMockDSTrans
    def test_purchase_catalog(self):
        catalog = get_purchase_catalog()
        assert_that(catalog, is_not(none()))
        assert_that(catalog, has_length(8))
        assert_that(isinstance(catalog, StoreCatalog), is_(True))
