#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import six

from zope import component
from zope import interface

from nti.store.payments.payeezy.interfaces import IPayeezyURLMap
from nti.store.payments.payeezy.interfaces import IPayeezyException
from nti.store.payments.payeezy.interfaces import IPayeezyConnectKey
from nti.store.payments.payeezy.interfaces import IPayeezyTokenException

PAYEEZY = u"payeezy"

PAY_URL = URL = 'URL'
TOKEN_URL = 'TOKEN_URL'


@interface.implementer(IPayeezyException)
class PayeezyException(Exception):
    pass


@interface.implementer(IPayeezyTokenException)
class PayeezyTokenException(PayeezyException):
    pass


def get_credentials(context):
    if isinstance(context, six.string_types):
        return component.getUtility(IPayeezyConnectKey, name=context)
    elif IPayeezyConnectKey.providedBy(context):
        return context
    return None


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
