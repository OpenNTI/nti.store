#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import component

from nti.store.interfaces import IPurchaseError

from nti.store.payments.payeezy import PAY_URL
from nti.store.payments.payeezy import TOKEN_URL

from nti.store.payments.payeezy import get_url_map
from nti.store.payments.payeezy import get_credentials

from nti.store.payments.payeezy.api.methods import Payeezy

from nti.store.payments.payeezy.interfaces import IPayeezyError
from nti.store.payments.payeezy.interfaces import IPayeezyConnectKey
from nti.store.payments.payeezy.interfaces import IPayeezyPurchaseError
from nti.store.payments.payeezy.interfaces import IPayeezyOperationError

from nti.store.payments.payeezy.model import PayeezyPurchaseError

from nti.store.purchase_attempt import get_providers

logger = __import__('logging').getLogger(__name__)


def get_api_key(purchase):
    providers = get_providers(purchase)
    provider = providers[0] if providers else '' # pick first provider
    payeezy_key = component.queryUtility(IPayeezyConnectKey, provider)
    return payeezy_key


def get_payeezy(context):
    url_map = get_url_map()
    credentials = get_credentials(context)
    result = Payeezy(api_key=credentials.APIKey,
                     api_secret=credentials.APISecret,
                     token=credentials.Token,
                     url=url_map[PAY_URL],
                     js_security_key=credentials.JSSecurityKey,
                     token_url=url_map[TOKEN_URL])
    return result


def adapt_to_purchase_error(e):
    """
    adapts an exception to a [purchase] error
    """
    if IPayeezyError.providedBy(e):
        result = IPayeezyOperationError(e, None)
    else:
        result = IPayeezyPurchaseError(e, None) or IPurchaseError(e, None)
    if result is None and isinstance(e, Exception):
        result = PayeezyPurchaseError(Type=u"PurchaseError")
        message = u' '.join(map(str, e.args()))
        result.Message = message
    return result


def safe_error_message(result):
    try:
        data = result.json()
        return data.get('message') or data.get('error')
    except Exception:  # pylint: disable=broad-except
        return None
