#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component
from zope import interface

from nti.store.payments.payeezy.interfaces import IPayeezyURLMap
from nti.store.payments.payeezy.interfaces import IPayeezyConnectKey


PAYEEZY = u"payeezy"

PAY_URL = URL = 'URL'
TOKEN_URL = 'TOKEN_URL'


def get_credentials(name):
    return component.getUtility(IPayeezyConnectKey, name=name)


def get_url_map():
    return component.getUtility(IPayeezyURLMap)


@interface.implementer(IPayeezyURLMap)
def live_urls():
    result = {
        PAY_URL: 'https://api.payeezy.com/v1/transactions',
        TOKEN_URL: 'https://api.payeezy.com/v1/securitytokens',
    }
    return result


@interface.implementer(IPayeezyURLMap)
def test_urls():
    result = {
        PAY_URL: 'https://api-cert.payeezy.com/v1/transactions',
        TOKEN_URL: 'https://api-cert.payeezy.com/v1/securitytokens',
    }
    return result
