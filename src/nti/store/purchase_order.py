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

from zope.cachedescriptors.property import CachedProperty

from zope.schema.fieldproperty import FieldPropertyStoredThroughField as FP

from nti.externalization.representation import WithRepr

from nti.schema.eqhash import EqHash

from nti.schema.field import SchemaConfigured

from nti.store.interfaces import IPriceable
from nti.store.interfaces import IPurchaseItem
from nti.store.interfaces import IPurchaseOrder

from nti.store.purchasable import get_purchasable
from nti.store.purchasable import get_providers as get_providers_from_purchasables

from nti.store.priceable import Priceable

from nti.store.utils import to_list
from nti.store.utils import copy_object
from nti.store.utils import MetaStoreObject


@interface.implementer(IPurchaseItem)
class PurchaseItem(Priceable):
    __metaclass__ = MetaStoreObject


def create_purchase_item(ntiid, quantity=1, cls=PurchaseItem):
    quantity = 1 if quantity is None else int(quantity)
    result = cls(NTIID=unicode(ntiid), Quantity=quantity)
    return result


@WithRepr
@EqHash('Items', 'Quantity')
@interface.implementer(IPurchaseOrder, IAttributeAnnotatable)
class PurchaseOrder(SchemaConfigured):

    __metaclass__ = MetaStoreObject

    Items = FP(IPurchaseOrder['Items'])
    Quantity = FP(IPurchaseOrder['Quantity'])  # override items quantity

    def item_factory(self, item):
        return create_purchase_item(ntiid=item)

    @CachedProperty('Items')
    def NTIIDs(self):
        result = tuple(x.NTIID for x in self.Items)
        return result

    def copy(self, *args, **kwargs):
        return copy_purchase_order(self, *args, **kwargs)

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
    return tuple(result)


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
    return tuple(result)


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


def copy_purchase_order(source, *args, **kwargs):
    items = to_list(kwargs.get('items'))
    if items:
        result = []
        for item in items:
            if IPriceable.providedBy(item):
                result.append(copy_object(item))
            else:
                item = source.item_factory(item)
                result.append(item)
        items = tuple(result)
    else:
        items = tuple(copy_object(x) for x in source.Items)

    result = source.__class__(Items=items, Quantity=source.Quantity)
    return result


def _purchase_order_copier(context):
    return copy_purchase_order
