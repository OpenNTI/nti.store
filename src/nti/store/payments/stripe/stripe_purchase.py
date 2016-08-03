#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from zope.schema.fieldproperty import FieldPropertyStoredThroughField as FP

from nti.schema.eqhash import EqHash

from nti.store.payments.stripe.interfaces import IStripePriceable
from nti.store.payments.stripe.interfaces import IStripePricedItem
from nti.store.payments.stripe.interfaces import IStripePurchaseItem
from nti.store.payments.stripe.interfaces import IStripePurchaseOrder

from nti.store.payments.stripe.utils import replace_items_coupon as replace_coupon

from nti.store.priceable import Priceable
from nti.store.priceable import copy_priceable

from nti.store.pricing import PricedItem

from nti.store.purchase_order import PurchaseItem
from nti.store.purchase_order import PurchaseOrder
from nti.store.purchase_order import copy_purchase_order
from nti.store.purchase_order import create_purchase_order

@interface.implementer(IStripePriceable)
@EqHash('Coupon', 'NTIID', 'Quantity')
class StripePriceable(Priceable):

	Coupon = FP(IStripePriceable['Coupon'])

	def copy(self, *args, **kwargs):
		return copy_stripe_priceable(self, *args, **kwargs)

def create_stripe_priceable(ntiid, quantity=None, coupon=None):
	quantity = 1 if quantity is None else int(quantity)
	result = StripePriceable(NTIID=unicode(ntiid), Quantity=quantity, Coupon=coupon)
	return result

def copy_stripe_priceable(source, *args, **kwargs):
	result = copy_priceable(source, *args, **kwargs)
	result.Coupon = kwargs.get('coupon') or source.Coupon
	return result

def _stripe_priceable_copier(context):
	return copy_stripe_priceable

@interface.implementer(IStripePricedItem)
@EqHash('Coupon', 'NTIID')
class StripePricedItem(PricedItem):

	Coupon = FP(IStripePricedItem['Coupon'])

	@classmethod
	def copy(cls, priced):
		return copy_stripe_priced_item(priced, cls=cls)

def copy_stripe_priced_item(priced, *args, **kwargs):
	cls = kwargs.get('cls') or priced.__class__
	result = cls(NTIID=priced.NTIID,
				 Quantity=priced.Quantity,
				 PurchaseFee=priced.PurchaseFee,
				 PurchasePrice=priced.PurchasePrice,
				 NonDiscountedPrice=priced.NonDiscountedPrice)
	result.Coupon = getattr(priced, 'Coupon', None)
	return result

def _stripe_priced_item_copier(context):
	return copy_stripe_priced_item

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

	def item_factory(self, item):
		return create_stripe_purchase_item(ntiid=item)

	def copy(self, *args, **kwargs):
		result = copy_stripe_purchase_order(self, *args, **kwargs)
		return result

	def __eq__(self, other):
		try:
			return 		super(StripePurchaseOrder, self).__eq__(other) \
					and self.Coupon == other.Coupon
		except AttributeError:
			return NotImplemented

	def __hash__(self):
		xhash = super(StripePurchaseOrder, self).__hash__()
		xhash ^= hash(self.Coupon)
		return xhash

def create_stripe_purchase_order(items, quantity=None, coupon=None):
	result = create_purchase_order(items, quantity, StripePurchaseOrder)
	if coupon is not None:
		replace_coupon(result, None)
		result.Coupon = coupon
	return result

def copy_stripe_purchase_order(source, *args, **kwargs):
	coupon = kwargs.pop('coupon', None)
	result = copy_purchase_order(source, *args, **kwargs)
	result.Coupon = coupon or source.Coupon
	return result

def _stripe_purchase_order_copier(context):
	return copy_stripe_purchase_order
