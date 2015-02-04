#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Defines purchase order.

.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from collections import Sequence

from zope import interface
from zope.annotation.interfaces import IAttributeAnnotatable
from zope.schema.fieldproperty import FieldPropertyStoredThroughField as FP

from nti.common.property import Lazy

from nti.externalization.representation import WithRepr

from nti.schema.schema import EqHash
from nti.schema.field import SchemaConfigured

from .utils import MetaStoreObject

from .priceable import Priceable

from .interfaces import IPurchaseItem
from .interfaces import IPurchaseOrder

from .purchasable import get_purchasable
from .purchasable import get_providers as get_providers_from_purchasables

@interface.implementer(IPurchaseItem)
class PurchaseItem(Priceable):
	__metaclass__ = MetaStoreObject

def create_purchase_item(ntiid, quantity=1, cls=PurchaseItem):
	quantity = 1 if quantity is None else int(quantity)
	result = cls(NTIID=unicode(ntiid), Quantity=quantity)
	return result

@interface.implementer(IPurchaseOrder, IAttributeAnnotatable)
@WithRepr
@EqHash('Items', 'Quantity')
class PurchaseOrder(SchemaConfigured):

	__metaclass__ = MetaStoreObject

	Items = FP(IPurchaseOrder['Items'])
	Quantity = FP(IPurchaseOrder['Quantity'])  # override items quantity

	@Lazy
	def NTIIDs(self):
		result = [x.NTIID for x in self.Items]
		return result

	def copy(self):
		items = tuple(item.copy() for item in self.Items)
		return self.__class__(Items=items, Quantity=self.Quantity)

	def __str__(self):
		return "(%s,%s)" % (self.Items, self.Quantity)

	def __getitem__(self, index):
		return self.Items[index]

	def __iter__(self):
		return iter(self.Items)
	
	def __len__(self):
		return len(self.Items)

def get_purchasables(order):
	"""
	return all purchasables for the associated order
	"""
	result = list()
	for item in order.NTIIDs:
		p = get_purchasable(item)
		if p is not None:
			result.append(p)
	return result

def get_providers(order):
	"""
	return all providers for the associated purchase
	"""
	purchasables = get_purchasables(order)
	result = get_providers_from_purchasables(purchasables)
	return result

def get_currencies(order):
	"""
	return all currencies for the associated purchase
	"""
	purchasables = get_purchasables(order)
	result = {p.Currency for p in purchasables}
	return list(result)

def replace_quantity(po_or_items, quantity):
	for item in getattr(po_or_items, 'Items', po_or_items):
		item.Quantity = quantity

def create_purchase_order(items=None, quantity=None, cls=PurchaseOrder):
	items = () if items is None else items
	items = (items,) if not isinstance(items, Sequence) else items
	if quantity is not None:
		quantity = int(quantity)
		replace_quantity(items, quantity)
	result = cls(Items=tuple(items), Quantity=quantity)
	return result
