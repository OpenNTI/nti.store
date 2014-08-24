#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Defines priced objects.

.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from . import MessageFactory as _

from zope import interface
from zope.mimetype.interfaces import IContentTypeAware

from nti.externalization.representation import WithRepr

from nti.schema.schema import EqHash
from nti.schema.field import SchemaConfigured
from nti.schema.fieldproperty import createDirectFieldProperties

from .utils import MetaStoreObject

from . import PricingException
from . import InvalidPurchasable

from .priceable import Priceable

from .interfaces import IPricedItem
from .interfaces import IPricingResults
from .interfaces import IPurchasablePricer

@interface.implementer(IPricedItem, IContentTypeAware)
@WithRepr
@EqHash('NTIID',)
class PricedItem(Priceable):
	__metaclass__ = MetaStoreObject
	createDirectFieldProperties(IPricedItem)


def create_priced_item(ntiid, purchase_price, purchase_fee=None,
					   non_discounted_price=None, quantity=1, currency='USD'):
	quantity = 1 if quantity is None else int(quantity)
	purchase_fee = float(purchase_fee) if purchase_fee is not None else None
	non_discounted_price = float(non_discounted_price) \
						   if non_discounted_price is not None else None
	result = PricedItem(NTIID=unicode(ntiid), PurchasePrice=float(purchase_price),
						PurchaseFee=purchase_fee, NonDiscountedPrice=non_discounted_price,
						Quantity=quantity, Currency=currency)
	return result

@interface.implementer(IPricingResults, IContentTypeAware)
@WithRepr
class PricingResults(SchemaConfigured):
	__metaclass__ = MetaStoreObject
	createDirectFieldProperties(IPricingResults)


def create_pricing_results(items=None, purchase_price=0.0, purchase_fee=0.0,
						   non_discounted_price=None, currency='USD'):
	items = list() if items is None else items
	purchase_fee = float(purchase_fee) if purchase_fee is not None else None
	non_discounted_price = 	float(non_discounted_price) \
							if non_discounted_price is not None else None
	result = PricingResults(Items=items, TotalPurchasePrice=purchase_price,
							TotalPurchaseFee=purchase_fee,
							TotalNonDiscountedPrice=non_discounted_price,
							Currency=currency)
	return result

@interface.implementer(IPurchasablePricer)
class DefaultPurchasablePricer(object):

	def calc_fee(self, amount, fee):
		fee_amount = 0.0
		if fee is not None:
			pct = fee / 100.0 if fee >= 1 else fee
			fee_amount = amount * pct
		return fee_amount

	def price(self, priceable):
		__traceback_info__ = priceable
		quantity = priceable.Quantity or 1
		purchasable = priceable.purchasable
		if purchasable is None:
			raise InvalidPurchasable("'%s' is an invalid purchasable NTIID" %
									priceable.NTIID)

		amount = purchasable.Amount
		new_amount = amount * quantity

		fee_amount = self.calc_fee(new_amount, purchasable.Fee)
		result = create_priced_item(ntiid=purchasable.NTIID,
									purchase_price=new_amount,
									purchase_fee=fee_amount,
									quantity=quantity,
									currency=priceable.Currency)
		return result

	def evaluate(self, priceables):
		currencies = set()
		result = create_pricing_results()
		for priceable in priceables:
			priced = self.price(priceable)
			result.Items.append(priced)
			currencies.add(priceable.Currency)
			result.TotalPurchaseFee += priced.PurchaseFee
			result.TotalPurchasePrice += priced.PurchasePrice

		if len(currencies) != 1:
			raise PricingException(_("Multi-Currency pricing is not supported"))

		result.Currency = currencies.pop()
		return result
