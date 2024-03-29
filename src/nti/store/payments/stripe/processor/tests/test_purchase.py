#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import none
from hamcrest import is_not
from hamcrest import has_key
from hamcrest import has_length
from hamcrest import assert_that
from hamcrest import has_property
does_not = is_not

import uuid
import stripe
import unittest

from zope.annotation import IAnnotations

from zope.component import eventtesting

from nti.dataserver.users import User

from nti.store import purchase_history

from nti.store.interfaces import PA_STATE_FAILED
from nti.store.interfaces import PA_STATE_SUCCESS

from nti.store.interfaces import IPurchaseAttemptFailed
from nti.store.interfaces import IPurchaseAttemptStarted
from nti.store.interfaces import IPurchaseAttemptSuccessful

from nti.store.payments.stripe.interfaces import STRIPE_CUSTOMER_KEY

from nti.store.payments.stripe.interfaces import IRegisterStripeToken
from nti.store.payments.stripe.interfaces import IRegisterStripeCharge
from nti.store.payments.stripe.interfaces import IStripeCustomerCreated
from nti.store.payments.stripe.interfaces import IStripeCustomerDeleted

from nti.store.payments.stripe.processor.purchase import PurchaseProcessor

from nti.dataserver.tests import mock_dataserver

from nti.store.payments.stripe.processor.tests import create_purchase
from nti.store.payments.stripe.processor.tests import TEST_WITH_STRIPE
from nti.store.payments.stripe.processor.tests import create_random_user
from nti.store.payments.stripe.processor.tests import StripeProcessorTestLayer
from nti.store.payments.stripe.processor.tests import create_and_register_purchase_attempt


class TestPurchaseProcessor(unittest.TestCase):

    layer = StripeProcessorTestLayer

    def setUp(self):
        super(TestPurchaseProcessor, self).setUp()
        self.manager = PurchaseProcessor()

    @mock_dataserver.WithMockDSTrans
    def test_create_token_and_charge(self):
        t = self.manager.create_card_token(number=u"5105105105105100",
                                           exp_month=u"11",
                                           exp_year=u"30",
                                           cvc=u"542",
                                           address=u"3001 Oak Tree #D16",
                                           city=u"Norman",
                                           zip=u"73072",
                                           state=u"OK",
                                           country=u"USA")
        assert_that(t, is_not(none()))

        c = self.manager.create_charge(100, card=t, description=u"my charge")
        assert_that(c, is_not(none()))

    create_purchase = create_purchase

    @mock_dataserver.WithMockDS
    def test_price_purchase_no_coupon(self):
        ds = self.ds

        with mock_dataserver.mock_db_trans(ds):
            item = self.book_id
            user = create_random_user()
            username = user.username
            purchase_id = create_and_register_purchase_attempt(username, item=item,
                                                               quantity=2,
                                                               processor=self.manager.name)

            result = self.manager.price_purchase(username=username,
                                                 purchase_id=purchase_id)
            assert_that(result, is_not(none()))
            assert_that(result.TotalPurchaseFee, is_(0))
            assert_that(result.TotalPurchasePrice, is_(200))
            assert_that(result.TotalNonDiscountedPrice, is_(200))

    @unittest.skipUnless(TEST_WITH_STRIPE, '')
    @mock_dataserver.WithMockDS
    def test_process_payment(self):
        ds = self.ds
        username, purchase_id, _, _ = self.create_purchase()

        with mock_dataserver.mock_db_trans(ds):
            pa = purchase_history.get_purchase_attempt(purchase_id, username)
            assert_that(pa.State, is_(PA_STATE_SUCCESS))

            assert_that(eventtesting.getEvents(IStripeCustomerCreated),
                        has_length(1))

            assert_that(eventtesting.getEvents(IPurchaseAttemptStarted),
                        has_length(1))

            assert_that(eventtesting.getEvents(IRegisterStripeToken),
                        has_length(1))
            assert_that(eventtesting.getEvents(IRegisterStripeCharge),
                        has_length(1))

            assert_that(eventtesting.getEvents(IPurchaseAttemptSuccessful),
                        has_length(1))

            # test payment charge
            charge = self.manager.get_payment_charge(purchase_id, username)
            assert_that(charge, is_not(none()))
            assert_that(charge, has_property("Amount", is_not(none())))
            assert_that(charge, has_property("Address", is_not(none())))
            assert_that(charge, has_property("Created", is_not(none())))
            assert_that(charge, has_property("Currency", is_not(none())))
            assert_that(charge, has_property("CardLast4", is_not(none())))
            user = User.get_user(username)
            assert_that(IAnnotations(user),
                        has_key(STRIPE_CUSTOMER_KEY))

            self.manager.delete_customer(username)

        assert_that(eventtesting.getEvents(IStripeCustomerDeleted),
                    has_length(1))

        with mock_dataserver.mock_db_trans(ds):
            user = User.get_user(username)
            assert_that(IAnnotations(user),
                        does_not(has_key(STRIPE_CUSTOMER_KEY)))

    @unittest.skipUnless(TEST_WITH_STRIPE, '')
    @mock_dataserver.WithMockDS
    def test_process_payment_coupon(self):

        code = str(uuid.uuid4()).split('-')[0]
        c = stripe.Coupon.create(percent_off=50, duration=u'once', id=code)

        ds = self.ds
        username, purchase_id, _, _ = \
                        self.create_purchase(amount=50, coupon=c.id)

        with mock_dataserver.mock_db_trans(ds):
            pa = purchase_history.get_purchase_attempt(purchase_id, username)
            assert_that(pa.State, is_(PA_STATE_SUCCESS))

        assert_that(eventtesting.getEvents(IStripeCustomerCreated),
                    has_length(1))

        assert_that(eventtesting.getEvents(IPurchaseAttemptStarted),
                    has_length(1))

        assert_that(eventtesting.getEvents(IRegisterStripeToken),
                    has_length(1))
        assert_that(eventtesting.getEvents(IRegisterStripeCharge),
                    has_length(1))

        assert_that(eventtesting.getEvents(IPurchaseAttemptSuccessful),
                    has_length(1))

        c.delete()

    @mock_dataserver.WithMockDS
    def test_fail_payment_invalid_token(self):
        ds = self.ds
        with mock_dataserver.mock_db_trans(ds):
            user = create_random_user()
            username = user.username

        with mock_dataserver.mock_db_trans(ds):
            item = self.book_id
            purchase_id = create_and_register_purchase_attempt(username,
                                                               item=item,
                                                               processor=self.manager.name)

        with self.assertRaises(Exception):
            self.manager.process_purchase(username=username,
                                          token=u"++invalidtoken++",
                                          purchase_id=purchase_id,
                                          expected_amount=100.0)

        assert_that(eventtesting.getEvents(IStripeCustomerCreated),
                    has_length(0))
        assert_that(eventtesting.getEvents(IPurchaseAttemptStarted),
                    has_length(1))
        assert_that(eventtesting.getEvents(IPurchaseAttemptFailed),
                    has_length(1))

        with mock_dataserver.mock_db_trans(ds):
            pa = purchase_history.get_purchase_attempt(purchase_id, username)
            assert_that(pa.State, is_(PA_STATE_FAILED))

    @mock_dataserver.WithMockDS
    def test_fail_payment_invalid_expected_amount(self):
        ds = self.ds
        with mock_dataserver.mock_db_trans(ds):
            user = create_random_user()
            username = user.username

        with mock_dataserver.mock_db_trans(ds):
            item = self.book_id
            purchase_id = create_and_register_purchase_attempt(username,
                                                               item=item,
                                                               processor=self.manager.name)

        with self.assertRaises(Exception):
            self.manager.process_purchase(username=username,
                                          token=u"++valid++",
                                          purchase_id=purchase_id,
                                          expected_amount=20000.0)

        assert_that(eventtesting.getEvents(IPurchaseAttemptFailed),
                    has_length(1))

        with mock_dataserver.mock_db_trans(ds):
            pa = purchase_history.get_purchase_attempt(purchase_id, username)
            assert_that(pa.State, is_(PA_STATE_FAILED))

    @mock_dataserver.WithMockDS
    def test_fail_payment_invalid_coupon(self):
        ds = self.ds
        with mock_dataserver.mock_db_trans(ds):
            with self.assertRaises(Exception):
                self.create_purchase(amount=50, coupon=u"++invalidcoupon++")
