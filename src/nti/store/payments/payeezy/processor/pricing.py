#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import component

from nti.store.interfaces import IPurchasablePricer

from nti.store.payments.payeezy import PAYEEZY

from nti.store.purchase_history import get_purchase_attempt

logger = __import__('logging').getLogger(__name__)


def price_order(order, name=PAYEEZY):
    pricer = component.getUtility(IPurchasablePricer, name=name)
    result = pricer.evaluate(order)
    return result


class PricingProcessor(object):

    @classmethod
    def do_pricing(cls, purchase_attempt):
        result = price_order(purchase_attempt.Order)
        return result

    @classmethod
    def price_purchase(cls, purchase_id, username=None):
        purchase = get_purchase_attempt(purchase_id, username)
        result = cls.do_pricing(purchase)
        return result
