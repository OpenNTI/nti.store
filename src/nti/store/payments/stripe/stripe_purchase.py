#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Defines stripe payment object.

.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface
from zope.schema.fieldproperty import FieldPropertyStoredThroughField as FP

from nti.schema.schema import EqHash

from ...pricing import PricedItem
from ...priceable import Priceable
from ...purchase_order import PurchaseItem
from ...purchase_order import PurchaseOrder
from ...purchase_order import create_purchase_order

from .interfaces import IStripePriceable
from .interfaces import IStripePricedItem
from .interfaces import IStripePurchaseItem
from .interfaces import IStripePurchaseOrder

@interface.implementer(IStripePriceable)
@EqHash('Coupon', 'NTIID', 'Quantity')
class StripePriceable(Priceable):

	Coupon = FP(IStripePriceable['Coupon'])

	def copy(self):
		result = super(StripePriceable, self).copy()
		result.Coupon = self.Coupon
		return result

def create_stripe_priceable(ntiid, quantity=None, coupon=None):
	quantity = 1 if quantity is None else int(quantity)
	result = StripePriceable(NTIID=unicode(ntiid), Quantity=quantity, Coupon=coupon)
	return result

@interface.implementer(IStripePricedItem)
@EqHash('Coupon', 'NTIID')
class StripePricedItem(PricedItem):

	Coupon = FP(IStripePricedItem['Coupon'])

	@classmethod
	def copy(cls, priced):
		result = cls(NTIID=priced.NTIID,
					 Quantity=priced.Quantity,
					 PurchaseFee=priced.PurchaseFee,
					 PurchasePrice=priced.PurchasePrice,
					 NonDiscountedPrice=priced.NonDiscountedPrice)
		result.Coupon = getattr(priced, 'Coupon', None)
		return result

# alias bwc
class StripePricedPurchasable(StripePricedItem):
	pass

@interface.implementer(IStripePurchaseItem)
class StripePurchaseItem(StripePriceable, PurchaseItem):
	pass

def create_stripe_purchase_item(ntiid, quantity=1, coupon=None):
	result = StripePurchaseItem(NTIID=ntiid, Quantity=quantity, Coupon=coupon)
	return result

@interface.implementer(IStripePurchaseOrder)
class StripePurchaseOrder(PurchaseOrder):

	Coupon = FP(IStripePurchaseOrder['Coupon'])  # overide items coupon

	def copy(self):
		result = super(StripePurchaseOrder, self).copy()
		result.Coupon = self.Coupon
		return result

	def __eq__(self, other):
		try:
			return 	super(StripePurchaseOrder, self).__eq__(other) and \
					self.Coupon == other.Coupon
		except AttributeError:
			return NotImplemented

	def __hash__(self):
		xhash = super(StripePurchaseOrder, self).__hash__()
		xhash ^= hash(self.Coupon)
		return xhash

def replace_coupon(po_or_items, coupon=None):
	for item in getattr(po_or_items, 'Items', po_or_items):
		item.Coupon = coupon

def create_stripe_purchase_order(items, quantity=None, coupon=None):
	result = create_purchase_order(items, quantity, StripePurchaseOrder)
	if coupon is not None:
		replace_coupon(result, None)
		result.Coupon = coupon
	return result
