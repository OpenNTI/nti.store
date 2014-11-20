#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import six
import stripe

from zope import component

from . import NoSuchStripeCoupon
from . import InvalidStripeCoupon

from .interfaces import IStripeConnectKey

from ... import PricingException

from ...interfaces import IPaymentProcessor

from ...pricing import create_pricing_results
from ...pricing import DefaultPurchasablePricer

from .stripe_purchase import StripePricedPurchasable

from . import STRIPE

def get_coupon(coupon=None, api_key=None, processor=STRIPE, registry=component):
	manager = registry.getUtility(IPaymentProcessor, name=processor)
	if coupon is not None and api_key:
		# stripe defines an 80 sec timeout for http requests
		# at this moment we are to wait for coupon validation
		if isinstance(coupon, six.string_types):
			try:
				coupon = manager.get_coupon(coupon, api_key=api_key)
			except stripe.InvalidRequestError as e:
				logger.error("Cannot retrieve coupon %s. %s", coupon, e)
				raise NoSuchStripeCoupon()
		if coupon is not None:
			validated_coupon = manager.validate_coupon(coupon, api_key=api_key)
			if not validated_coupon:
				raise InvalidStripeCoupon()
	return coupon
	
class StripePurchasablePricer(DefaultPurchasablePricer):

	processor = STRIPE

	def get_coupon(self, coupon=None, api_key=None, registry=component):
		result = get_coupon(coupon=coupon, 
							api_key=api_key, 
							processor=self.processor,
							registry=component)
		return result

	def price(self, priceable, registry=component):
		priced = super(StripePurchasablePricer, self).price(priceable)
		priced = StripePricedPurchasable.copy(priced)
		coupon = getattr(priceable, 'Coupon', None)

		manager = registry.getUtility(IPaymentProcessor, name=self.processor)
		stripe_key = registry.queryUtility(IStripeConnectKey, priced.Provider)

		purchase_price = priced.PurchasePrice

		if coupon is not None and stripe_key:
			priced.Coupon = self.get_coupon(coupon=coupon, 
											api_key=stripe_key.PrivateKey, 
											registry=registry)
			if priced.Coupon is not None:
				priced.NonDiscountedPrice = purchase_price
				purchase_price = manager.apply_coupon(purchase_price, priced.Coupon)
				priced.PurchasePrice = purchase_price
				priced.PurchaseFee = self.calc_fee(purchase_price, priceable.Fee)
		return priced

	def evaluate(self, priceables, registry=component):
		providers = set()
		currencies = set()
		result = create_pricing_results(non_discounted_price=0.0)
		for priceable in priceables:
			currencies.add(priceable.Currency)
			providers.add(priceable.Provider)
			priced = self.price(priceable, registry)
			result.Items.append(priced)
			result.TotalPurchaseFee += priced.PurchaseFee
			result.TotalPurchasePrice += priced.PurchasePrice
			result.TotalNonDiscountedPrice += \
						priced.NonDiscountedPrice or priced.PurchasePrice

		if len(currencies) != 1:
			raise PricingException("Multi-Currency pricing is not supported")
		result.Currency = currencies.pop()

		# apply coupon at the 'order' level
		coupon = getattr(priceables, 'Coupon', None)
		if coupon is not None:
			if len(providers) != 1:
				raise PricingException("Multi-Provider coupon purchase is not supported")

			provider = providers.pop()
			stripe_key = registry.queryUtility(IStripeConnectKey, provider)
			coupon = self.get_coupon(coupon, stripe_key.PrivateKey) if stripe_key else None
			manager = registry.getUtility(IPaymentProcessor, name=self.processor)
			if coupon is not None:
				result.NonDiscountedPrice = result.TotalPurchasePrice
				purchase_price = manager.apply_coupon(result.TotalPurchasePrice, coupon)
				result.TotalPurchasePrice = purchase_price
				result.TotalPurchaseFee = self.calc_fee(purchase_price, priceable.Fee)

		return result
