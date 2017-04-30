#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import none
from hamcrest import is_not
from hamcrest import has_entry
from hamcrest import assert_that
from hamcrest import has_entries
does_not = is_not

import re
import unittest

import simplejson

from nti.store.payments.payeezy import PAY_URL
from nti.store.payments.payeezy import TOKEN_URL
from nti.store.payments.payeezy import get_url_map
from nti.store.payments.payeezy import get_credentials

from nti.store.payments.payeezy.api.methods import Payeezy

from nti.store.tests import SharedConfiguringTestLayer


class TestMethods(unittest.TestCase):

    layer = SharedConfiguringTestLayer

    def _credentials(self):
        return get_credentials("NTI-TEST")

    def _get_payeezy(self):
        url_map = get_url_map()
        credentials = self._credentials()
        result = Payeezy(api_key=credentials.APIKey,
                         api_secret=credentials.APISecret,
                         token=credentials.Token,
                         url=url_map[PAY_URL],
                         js_security_key=credentials.JSSecurityKey,
                         token_url=url_map[TOKEN_URL])
        return result

    def test_purchase(self):
        payeezy = self._get_payeezy()
        result = payeezy.purchase(100, "USD",
                                  card_type="visa",
                                  cardholder_name="Ichigo Kurosaki",
                                  card_number="4012000033330026",
                                  card_expiry="0930",
                                  card_cvv="019")
        data = result.json()
        assert_that(data,
                    has_entries('amount', '100',
                                'correlation_id', is_not(none()),
                                'currency', 'USD',
                                'method', 'credit_card',
                                'token',
                                has_entries(
                                    'token_data',
                                        has_entry('value', is_not(none())),
                                    'token_type', 'FDToken'),
                                'transaction_id', is_not(none()),
                                'transaction_status', 'approved',
                                'transaction_tag', is_not(none()),
                                'transaction_type', 'purchase',
                                'validation_status', 'success'))

    def test_fd_token(self):
        callback = 'callback'
        payeezy = self._get_payeezy()
        result = payeezy.fd_token(card_type="visa",
                                  cardholder_name="Ichigo Kurosaki",
                                  card_number="4012000033330026",
                                  card_expiry="0930",
                                  card_cvv="019",
                                  street="Bleach Way",
                                  city="Norman",
                                  state="OK",
                                  zip_code="73072",
                                  country="USA",
                                  callback=callback)

        assert_that(result.status_code, is_(200))
        text = re.sub(r'[\s\n]', '', result.text)
        text = text[len(callback) + 1:-1]
        data = simplejson.loads(text)
        assert_that(data,
                    has_entries('status', 201,
                                'results',
                                has_entries('correlation_id', is_not(none()),
                                            'status', 'success',
                                            'type', 'FDToken',
                                            'token',
                                            has_entries('value', is_not(none()),
                                                        'type', 'visa'))))
