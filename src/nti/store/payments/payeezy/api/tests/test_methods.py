#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_not
does_not = is_not

import unittest

from nti.store.payments.payeezy import PAY_URL
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
                         url=url_map[PAY_URL])
        return result
        
    def test_purchase(self):
        payeezy = self._get_payeezy()
        # from IPython.terminal.debugger import set_trace
        # set_trace()
        print(payeezy.purchase(100, "USD", 
                         card_type="visa", 
                         cardholder_name="Ichigo Kurosaki",
                         card_number="4012000033330026", 
                         card_expiry="0930", 
                         card_cvv="019"))