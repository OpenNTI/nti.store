#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import none
from hamcrest import is_not
from hamcrest import has_length
from hamcrest import assert_that

from nti.testing.matchers import is_empty

import unittest

from nti.store.index import StoreCatalog
from nti.store.index import PurchasableCatalog

from nti.store.index import create_purchase_catalog
from nti.store.index import create_purchasable_catalog

from nti.store.store import get_purchasable

from nti.store.tests import SharedConfiguringTestLayer


class TestPurchaseIndex(unittest.TestCase):

    layer = SharedConfiguringTestLayer

    def test_purchase_catalog(self):
        catalog = create_purchase_catalog()
        assert_that(catalog, is_not(none()))
        assert_that(catalog, has_length(8))
        assert_that(isinstance(catalog, StoreCatalog), is_(True))

    def test_purchasable_catalog(self):
        catalog = create_purchasable_catalog()
        assert_that(catalog, is_not(none()))
        assert_that(catalog, has_length(10))
        assert_that(isinstance(catalog, PurchasableCatalog), is_(True))

        ntiid = 'tag:nextthought.com,2011-10:NextThought-purchasable-HelpCenter'
        purchasable = get_purchasable(ntiid)
        purchasable.Label = u'HelpCenter'
        catalog.index_doc(1, purchasable)

        for query in (
                {'ntiid': {'any_of': (ntiid,)}},
                {'public': {'any_of': (True,)}},
                {'currency': {'any_of': ('USD',)}},
                {'label': {'any_of': ('HelpCenter',)}},
                {'provider': {'any_of': ('NTI-TEST',)}},
                {'mimeType': {'any_of': ('application/vnd.nextthought.store.purchasable',)}},
                {'items': {'any_of': ('tag:nextthought.com,2011-10:NextThought-HTML-NextThoughtHelpCenter.nextthought_help_center',)}}):
            results = catalog.apply(query) or ()
            assert_that(results, is_not(is_empty()))
