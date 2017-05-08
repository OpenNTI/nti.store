#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from nti.store.payments.payeezy import PAY_URL
from nti.store.payments.payeezy import TOKEN_URL

from nti.store.payments.payeezy import get_url_map
from nti.store.payments.payeezy import get_credentials

from nti.store.payments.payeezy.api.methods import Payeezy


def get_payeezy(name):
    url_map = get_url_map()
    credentials = get_credentials(name)
    result = Payeezy(api_key=credentials.APIKey,
                     api_secret=credentials.APISecret,
                     token=credentials.Token,
                     url=url_map[PAY_URL],
                     js_security_key=credentials.JSSecurityKey,
                     token_url=url_map[TOKEN_URL])
    return result
