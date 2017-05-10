#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component

from nti.store.interfaces import IPurchasablePricer

from nti.store.payments.stripe import STRIPE

from nti.store.payments.stripe.processor.base import BaseProcessor

from nti.store.purchase_history import get_purchase_attempt


def price_order(order):
    pricer = component.getUtility(IPurchasablePricer, name=STRIPE)
    result = pricer.evaluate(order)
    return result


def price_purchase(purchase_attempt):
    result = price_order(purchase_attempt.Order)
    return result


class PricingProcessor(BaseProcessor):

    def do_pricing(self, purchase_attempt):
        result = price_purchase(purchase_attempt)
        return result

    def price_purchase(self, purchase_id, username=None):
        purchase = get_purchase_attempt(purchase_id, username)
        result = self.do_pricing(purchase)
        return result
