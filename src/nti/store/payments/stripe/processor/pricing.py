#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component

from nti.store.interfaces import IPurchasablePricer

from nti.store.payments.stripe import STRIPE

from nti.store.payments.stripe.processor.base import BaseProcessor

from nti.store.purchase_history import get_purchase_attempt


def price_order(order, name=STRIPE, registry=component):
    pricer = registry.getUtility(IPurchasablePricer, name=name)
    result = pricer.evaluate(order, registry=registry)
    return result


def price_purchase(purchase_attempt, name=STRIPE, registry=component):
    result = price_order(purchase_attempt.Order, registry=registry)
    return result


class PricingProcessor(BaseProcessor):

    def do_pricing(self, purchase_attempt, registry=component):
        result = price_purchase(purchase_attempt,
                                name=self.name,
                                registry=registry)
        return result
    _do_pricing = do_pricing  # BWC

    def price_purchase(self, purchase_id, username, registry=component):
        purchase = get_purchase_attempt(purchase_id, username)
        result = self.do_pricing(purchase, registry=registry)
        return result
