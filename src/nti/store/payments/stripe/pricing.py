#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import six
import stripe

from zope import component

from nti.store import PricingException

from nti.store import MessageFactory as _

from nti.store.interfaces import IPaymentProcessor

from nti.store.payments.stripe import STRIPE

from nti.store.payments.stripe import NoSuchStripeCoupon
from nti.store.payments.stripe import InvalidStripeCoupon

from nti.store.payments.stripe.interfaces import IStripeConnectKey

from nti.store.payments.stripe.stripe_purchase import StripePricedPurchasable

from nti.store.pricing import create_pricing_results
from nti.store.pricing import DefaultPurchasablePricer


def get_coupon(coupon=None, api_key=None, processor=STRIPE):
    manager = component.getUtility(IPaymentProcessor, name=processor)
    if coupon is not None and api_key:
        # stripe defines an 80 sec timeout for http requests
        # at this moment we are to wait for coupon validation
        if isinstance(coupon, six.string_types):
            try:
                coupon = manager.get_coupon(coupon, api_key=api_key)
            except stripe.error.InvalidRequestError as e:
                logger.error("Cannot retrieve coupon %s. %s", coupon, e)
                raise NoSuchStripeCoupon()
        if coupon is not None:
            validated_coupon = manager.validate_coupon(coupon, api_key=api_key)
            if not validated_coupon:
                raise InvalidStripeCoupon()
    return coupon


class StripePurchasablePricer(DefaultPurchasablePricer):

    processor = STRIPE

    def get_coupon(self, coupon=None, api_key=None):
        result = get_coupon(coupon=coupon,
                            api_key=api_key,
                            processor=self.processor)
        return result

    def price(self, priceable):
        priced = super(StripePurchasablePricer, self).price(priceable)
        priced = StripePricedPurchasable.copy(priced)
        coupon = getattr(priceable, 'Coupon', None)

        manager = component.getUtility(IPaymentProcessor, name=self.processor)
        stripe_key = component.queryUtility(IStripeConnectKey, priced.Provider)

        purchase_price = priced.PurchasePrice

        if coupon is not None and stripe_key:
            priced.Coupon = self.get_coupon(coupon=coupon,
                                            api_key=stripe_key.PrivateKey,)
            if priced.Coupon is not None:
                priced.NonDiscountedPrice = purchase_price
                purchase_price = manager.apply_coupon(purchase_price, 
                                                      priced.Coupon)
                priced.PurchasePrice = purchase_price
                priced.PurchaseFee = self.calc_fee(purchase_price,
                                                   priceable.Fee)
        return priced

    def evaluate(self, priceables):
        providers = set()
        currencies = set()
        result = create_pricing_results(non_discounted_price=0.0)
        for priceable in priceables:
            currencies.add(priceable.Currency)
            providers.add(priceable.Provider)
            priced = self.price(priceable)
            # track prices
            result.Items.append(priced)
            result.TotalPurchaseFee += priced.PurchaseFee
            result.TotalPurchasePrice += priced.PurchasePrice
            # total price
            total = priced.NonDiscountedPrice or priced.PurchasePrice
            result.TotalNonDiscountedPrice += total

        if len(currencies) != 1:
            msg = _(u"Multi-Currency pricing is not supported.")
            raise PricingException(msg)
        result.Currency = currencies.pop()

        # apply coupon at the 'order' level
        coupon = getattr(priceables, 'Coupon', None)
        if coupon is not None:
            if len(providers) != 1:
                msg = _(u"Multi-Provider coupon purchase is not supported.")
                raise PricingException(msg)

            provider = providers.pop()
            stripe_key = component.queryUtility(IStripeConnectKey, provider)
            if stripe_key:
                coupon = self.get_coupon(coupon, stripe_key.PrivateKey)
            else:
                coupon = None
            manager = component.getUtility(IPaymentProcessor, 
                                           name=self.processor)
            if coupon is not None:
                result.NonDiscountedPrice = result.TotalPurchasePrice
                purchase_price = manager.apply_coupon(result.TotalPurchasePrice, 
                                                      coupon)
                result.TotalPurchasePrice = purchase_price
                result.TotalPurchaseFee = self.calc_fee(purchase_price, 
                                                        priceable.Fee)

        return result
