#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from functools import total_ordering

from zope import interface

from zope.annotation.interfaces import IAttributeAnnotatable

from zope.schema.fieldproperty import FieldPropertyStoredThroughField as FP

from nti.externalization.representation import WithRepr

from nti.property.property import alias

from nti.schema.eqhash import EqHash

from nti.schema.field import SchemaConfigured

from nti.schema.fieldproperty import AdaptingFieldProperty
from nti.schema.fieldproperty import createDirectFieldProperties

from nti.store.interfaces import IPrice
from nti.store.interfaces import IItemBundle
from nti.store.interfaces import IRefundError
from nti.store.interfaces import IPricingError
from nti.store.interfaces import IPurchaseError
from nti.store.interfaces import IRedemptionError

from nti.store.utils import MetaStoreObject


@WithRepr
@EqHash('NTIID',)
@interface.implementer(IItemBundle, IAttributeAnnotatable)
class ItemBundle(SchemaConfigured):
    createDirectFieldProperties(IItemBundle)

    Label = FP(IItemBundle['Label'])
    Description = AdaptingFieldProperty(IItemBundle['Description'])

    id = ntiid = alias('NTIID')

    def __str__(self):
        return self.NTIID
ContentBundle = ItemBundle  # BWC


@WithRepr
@EqHash('Type', 'Code', 'Message')
@interface.implementer(IPricingError)
class PricingError(SchemaConfigured, BaseException):
    __metaclass__ = MetaStoreObject
    createDirectFieldProperties(IPricingError)

    def __str__(self):
        return self.Message


def create_pricing_error(message, type_=None, code=None):
    result = PricingError(Message=message, Type=type_, Code=code)
    return result


@WithRepr
@EqHash('Type', 'Code', 'Message')
@interface.implementer(IPurchaseError)
class PurchaseError(SchemaConfigured, BaseException):
    __metaclass__ = MetaStoreObject
    createDirectFieldProperties(IPurchaseError)

    def __str__(self):
        return self.Message


def create_purchase_error(message, type_=None, code=None):
    result = PurchaseError(Message=message, Type=type_, Code=code)
    return result


@WithRepr
@EqHash('Type', 'Code', 'Message')
@interface.implementer(IRedemptionError)
class RedemptionError(SchemaConfigured):
    __metaclass__ = MetaStoreObject
    createDirectFieldProperties(IRedemptionError)

    def __str__(self):
        return self.Message


def create_redemption_error(message, type_=None, code=None):
    result = RedemptionError(Message=message, Type=type_, Code=code)
    return result


@WithRepr
@EqHash('Type', 'Code', 'Message')
@interface.implementer(IRefundError)
class RefundError(SchemaConfigured, BaseException):
    __metaclass__ = MetaStoreObject
    createDirectFieldProperties(IRefundError)

    def __str__(self):
        return self.Message


def create_refund_error(message, type_=None, code=None):
    result = RefundError(Message=message, Type=type_, Code=code)
    return result


@WithRepr
@total_ordering
@EqHash('Amount', 'Currency')
@interface.implementer(IPrice)
class Price(SchemaConfigured):
    createDirectFieldProperties(IPrice)

    amount = alias('Amount')
    currency = alias('Currency')

    def __lt__(self, other):
        try:
            return (self.Amount, self.Currency) < (other.Amount, other.Currency)
        except AttributeError:  # pragma: no cover
            return NotImplemented

    def __gt__(self, other):
        try:
            return (self.Amount, self.Currency) > (other.Amount, other.Currency)
        except AttributeError:  # pragma: no cover
            return NotImplemented
