#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import six

from zope import interface

from zope.mimetype.interfaces import IContentTypeAware

from nti.externalization.representation import WithRepr

from nti.schema.eqhash import EqHash

from nti.schema.field import SchemaConfigured

from nti.schema.fieldproperty import createDirectFieldProperties

from nti.store import MessageFactory as _

from nti.store import ROUND_DECIMAL
from nti.store import PricingException
from nti.store import InvalidPurchasable

from nti.store.interfaces import IPricedItem
from nti.store.interfaces import IPricingResults
from nti.store.interfaces import IPurchasablePricer

from nti.store.priceable import Priceable

from nti.store.utils import MetaStoreObject

logger = __import__('logging').getLogger(__name__)


@six.add_metaclass(MetaStoreObject)
@WithRepr
@EqHash('NTIID',)
@interface.implementer(IPricedItem, IContentTypeAware)
class PricedItem(Priceable):
    createDirectFieldProperties(IPricedItem)


def create_priced_item(ntiid, purchase_price, purchase_fee=None,
                       non_discounted_price=None, quantity=1, currency=u'USD'):
    quantity = 1 if quantity is None else int(quantity)
    purchase_fee = float(purchase_fee) if purchase_fee is not None else None
    if non_discounted_price is not None:
        non_discounted_price = float(non_discounted_price)
    else:
        non_discounted_price = None
    result = PricedItem(NTIID=ntiid,
                        Currency=currency,
                        Quantity=quantity,
                        PurchaseFee=purchase_fee,
                        PurchasePrice=float(purchase_price),
                        NonDiscountedPrice=non_discounted_price)
    return result


@six.add_metaclass(MetaStoreObject)
@WithRepr
@interface.implementer(IPricingResults, IContentTypeAware)
class PricingResults(SchemaConfigured):
    createDirectFieldProperties(IPricingResults)


def create_pricing_results(items=None, purchase_price=0.0, purchase_fee=0.0,
                           non_discounted_price=None, currency=u'USD'):
    items = list() if items is None else items
    purchase_fee = float(purchase_fee) if purchase_fee is not None else None
    if non_discounted_price is not None:
        non_discounted_price = float(non_discounted_price)
    else:
        non_discounted_price = None
    result = PricingResults(Items=items,
                            Currency=currency,
                            TotalPurchaseFee=purchase_fee,
                            TotalPurchasePrice=purchase_price,
                            TotalNonDiscountedPrice=non_discounted_price)
    return result


@interface.implementer(IPurchasablePricer)
class DefaultPurchasablePricer(object):

    def calc_fee(self, amount, fee):
        fee_amount = 0.0
        if fee is not None:
            pct = fee / 100.0 if fee >= 1 else fee
            fee_amount = round(amount * pct, ROUND_DECIMAL)
        return fee_amount

    def price(self, priceable, registry=None):
        __traceback_info__ = priceable
        quantity = priceable.Quantity or 1
        purchasable = priceable.purchasable
        if purchasable is None:
            raise InvalidPurchasable("'%s' is an invalid purchasable NTIID" %
                                     priceable.NTIID)

        amount = purchasable.Amount
        new_amount = round(amount * quantity, ROUND_DECIMAL)

        fee_amount = self.calc_fee(new_amount, purchasable.Fee)
        result = create_priced_item(ntiid=purchasable.NTIID,
                                    purchase_price=new_amount,
                                    purchase_fee=fee_amount,
                                    quantity=quantity,
                                    currency=priceable.Currency)
        return result

    def evaluate(self, priceables, registry=None):
        currencies = set()
        result = create_pricing_results()
        for priceable in priceables:
            priced = self.price(priceable, registry=registry)
            result.Items.append(priced)
            currencies.add(priceable.Currency)
            result.TotalPurchaseFee += priced.PurchaseFee
            result.TotalPurchasePrice += priced.PurchasePrice
        result.TotalNonDiscountedPrice = result.TotalPurchasePrice
        if len(currencies) != 1:
            msg = _(u"Multi-Currency pricing is not supported")
            raise PricingException(msg)
        result.Currency = currencies.pop()
        return result
