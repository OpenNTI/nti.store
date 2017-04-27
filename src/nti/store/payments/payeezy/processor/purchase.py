#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component

from zope.event import notify

from nti.site.interfaces import ISiteTransactionRunner

from nti.store import PurchaseException

from nti.store.interfaces import PurchaseAttemptFailed
from nti.store.interfaces import PurchaseAttemptStarted

from nti.store.payments.payeezy.processor.pricing import PricingProcessor

from nti.store.store import get_purchase_attempt


def get_transaction_runner():
    result = component.getUtility(ISiteTransactionRunner)
    return result


def _start_purchase(purchase_id, token, username=None):
    purchase = get_purchase_attempt(purchase_id, username)
    if purchase is None:
        msg = "Could not find purchase attempt %s" % purchase_id
        raise PurchaseException(msg)

    if not purchase.is_pending():
        notify(PurchaseAttemptStarted(purchase))


def _fail_purchase(purchase_id, error, username=None):
    purchase = get_purchase_attempt(purchase_id, username)
    if purchase is not None:
        notify(PurchaseAttemptFailed(purchase, error))


def _get_purchase(purchase_id, username=None):
    purchase = get_purchase_attempt(purchase_id, username)
    return purchase


class PurchaseProcessor(PricingProcessor):
    pass
