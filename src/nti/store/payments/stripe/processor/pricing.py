#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Stripe purchase pricing functionalilty.

.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component

from ....interfaces import IPurchasablePricer
from ....purchase_history import get_purchase_attempt

from .. import STRIPE

from .base import BaseProcessor

def price_order(order, name=STRIPE, registry=component):
	pricer = component.getUtility(IPurchasablePricer, name=name)
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
