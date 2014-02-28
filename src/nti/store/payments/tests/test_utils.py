#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

#disable: accessing protected members, too many methods
#pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import assert_that

import unittest

from zope.schema import ValidationError

from nti.store.payments import utils

from nose.tools import assert_raises

class TestPaymentUtils(unittest.TestCase):

	def test_is_valid_creditcard_number(self):
		assert_that(utils.is_valid_creditcard_number("4111-1111-1111-1111"), is_(True))
		assert_that(utils.is_valid_creditcard_number("4111 1111 1111 1112"), is_(False))
		assert_that(utils.is_valid_creditcard_number("5105105105105100"), is_(True))
		assert_that(utils.is_valid_creditcard_number(5105105105105100), is_(True))
		assert_that(utils.is_valid_creditcard_number("111"), is_(False))
		assert_that(utils.is_valid_creditcard_number("5105105105105XY0"), is_(False))

	def test_validate_credit_card(self):
		utils.validate_credit_card(5105105105105100, "01", "12", "647")
		with assert_raises(ValidationError):
			utils.validate_credit_card(5105105105105101, "01", "12", "647")

		with assert_raises(ValidationError):
			utils.validate_credit_card("5105105105105100", "1", "12", "647")

		with assert_raises(ValidationError):
			utils.validate_credit_card("5105105105105100", "10", "3", "647")

		with assert_raises(ValidationError):
			utils.validate_credit_card("5105105105105100", "01", "13", "xx")
