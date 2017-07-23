#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import none
from hamcrest import is_in
from hamcrest import is_not
from hamcrest import contains
from hamcrest import not_none
from hamcrest import has_length
from hamcrest import assert_that
from hamcrest import has_property
import unittest

from nti.dataserver.users import User

from nti.externalization.internalization import find_factory_for
from nti.externalization.internalization import update_from_external_object

from nti.ntiids.ntiids import find_object_with_ntiid

from nti.schema.interfaces import find_most_derived_interface

from nti.store.interfaces import IPurchasable
from nti.store.interfaces import IPurchasableChoiceBundle

from nti.store.purchasable import get_purchasable
from nti.store.purchasable import PurchasableChoiceBundle
from nti.store.purchasable import expand_purchase_item_ids

from nti.store.purchase_attempt import create_purchase_attempt

from nti.store.purchase_order import create_purchase_item
from nti.store.purchase_order import create_purchase_order

from nti.store.tests import SharedConfiguringTestLayer


class TestPurchasable(unittest.TestCase):

    layer = SharedConfiguringTestLayer

    processor = 'stripe'

    def _create_user(self, username=u'nt@nti.com', password=u'temp001'):
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

    def test_internalization(self):
        ext_obj = {
            'Amount': 300.0,
            'Author': u'CMU',
            'BulkPurchase': True,
            'Class': 'Purchasable',
            'Currency': u'USD',
            'Description': u'04-630: Computer Science for Practicing Engineers',
            'Discountable': True,
            'Fee': None,
            'Giftable': False,
            'Icon': u'http://cmu.edu/',
            'IsPurchasable': True,
            'Items': [u'tag:nextthought.com,2011-10:CMU-HTML-04630_main.04_630:_computer_science_for_practicing_engineers'],
            'License': u'1 Year License',
            'MimeType': u'application/vnd.nextthought.store.purchasable',
            'NTIID': u'tag:nextthought.com,2011-10:CMU-purchasable-computer_science_for_practicing_engineer',
            'Provider': u'CMU',
            'Public': True,
            'PurchaseCutOffDate': u"2015-06-13T04:59:00+00:00",
            'RedeemCutOffDate': u"2015-06-13T04:59:00+00:00",
            'Redeemable': False}

        factory = find_factory_for(ext_obj)
        assert_that(factory, is_not(none()))
        result = factory()
        update_from_external_object(result, ext_obj)

        assert_that(result, has_property('Fee', is_(none())))
        assert_that(result, has_property('Public', is_(True)))
        assert_that(result, has_property('Amount', is_(300.0)))
        assert_that(result, has_property('Author', is_('CMU')))
        assert_that(result, has_property('Provider', is_('CMU')))
        assert_that(result, has_property('Currency', is_('USD')))
        assert_that(result, has_property('Giftable', is_(False)))
        assert_that(result, has_property('Redeemable', is_(False)))
        assert_that(result, has_property('BulkPurchase', is_(True)))
        assert_that(result, has_property('Discountable', is_(True)))
        assert_that(result, has_property('RedeemCutOffDate', not_none()))
        assert_that(result, has_property('PurchaseCutOffDate', not_none()))
        assert_that(result, has_property('Icon', is_('http://cmu.edu/')))
        assert_that(result, has_property('License', is_('1 Year License')))
        assert_that(result,
                    has_property('Description', is_('04-630: Computer Science for Practicing Engineers')))
        assert_that(result,
                    has_property('NTIID', is_('tag:nextthought.com,2011-10:CMU-purchasable-computer_science_for_practicing_engineer')))
        assert_that(result, has_property('Items', has_length(1)))
        assert_that(result,
                    has_property('Items', contains('tag:nextthought.com,2011-10:CMU-HTML-04630_main.04_630:_computer_science_for_practicing_engineers')))

    def test_interface(self):
        p = PurchasableChoiceBundle()
        iface = find_most_derived_interface(p, IPurchasable)
        assert_that(iface, is_(IPurchasableChoiceBundle))
