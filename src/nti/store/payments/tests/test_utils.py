#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import assert_that

from nose.tools import assert_raises

import unittest

from zope.schema import ValidationError

from nti.store.payments.utils import credit_card_type
from nti.store.payments.utils import validate_credit_card
from nti.store.payments.utils import is_valid_creditcard_number

from nti.store.tests import SharedConfiguringTestLayer


class TestPaymentUtils(unittest.TestCase):

    layer = SharedConfiguringTestLayer

    def test_is_valid_creditcard_number(self):
        assert_that(is_valid_creditcard_number("5418998592489835"),
                    is_(True))
        assert_that(is_valid_creditcard_number("5504 0214 5972 7991"),
                    is_(False))
        assert_that(is_valid_creditcard_number(4556919296095038),
                    is_(True))
        assert_that(is_valid_creditcard_number("111"),
                    is_(False))
        assert_that(is_valid_creditcard_number("5105105105105XY0"),
                    is_(False))

    def test_validate_credit_card(self):

        validate_credit_card(348728112862781, "01", "12", "647")

        with assert_raises(ValidationError):
            validate_credit_card(5105105105105101, "01", "12", "647")

        with assert_raises(ValidationError):
            validate_credit_card("5105105105105100", "1", "12", "647")

        with assert_raises(ValidationError):
            validate_credit_card("5105105105105100", "10", "3", "647")

        with assert_raises(ValidationError):
            validate_credit_card("5105105105105100", "01", "13", "xx")
            
    def test_credit_card_type(self):
        assert_that(credit_card_type('4024007141696'), is_('VISA'))
        assert_that(credit_card_type(5424000000000015), is_('MASTERCARD'))
        assert_that(credit_card_type('370000000000002'), is_('AMEX'))
        assert_that(credit_card_type('6011000000000012'), is_('Discover'))
