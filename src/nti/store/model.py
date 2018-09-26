#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from functools import total_ordering

import six

from zope import interface

from zope.annotation.interfaces import IAttributeAnnotatable

from zope.schema.fieldproperty import FieldPropertyStoredThroughField as FP

from nti.externalization.representation import WithRepr

from nti.property.property import alias

from nti.schema.eqhash import EqHash

from nti.schema.fieldproperty import AdaptingFieldProperty
from nti.schema.fieldproperty import createDirectFieldProperties

from nti.schema.schema import SchemaConfigured

from nti.store.interfaces import IPrice
from nti.store.interfaces import IItemBundle
from nti.store.interfaces import IRefundError
from nti.store.interfaces import IPricingError
from nti.store.interfaces import IPurchaseError
from nti.store.interfaces import IRedemptionError

from nti.store.utils import MetaStoreObject

logger = __import__('logging').getLogger(__name__)


@WithRepr
@EqHash('NTIID',)
@interface.implementer(IItemBundle, IAttributeAnnotatable)
class ItemBundle(SchemaConfigured):
    createDirectFieldProperties(IItemBundle)

    Label = FP(IItemBundle['Label'])
    Description = AdaptingFieldProperty(IItemBundle['Description'])

    id = ntiid = alias('NTIID')

    def __str__(self):
        # pylint: disable=no-member
        return self.NTIID
ContentBundle = ItemBundle  # BWC


@six.add_metaclass(MetaStoreObject)
@WithRepr
@EqHash('Type', 'Code', 'Message')
@interface.implementer(IPricingError)
class PricingError(SchemaConfigured, BaseException):

    createDirectFieldProperties(IPricingError)

    def __str__(self):
        # pylint: disable=no-member
        return self.Message


def create_pricing_error(message, type_=None, code=None):
    result = PricingError(Message=message, Type=type_, Code=code)
    return result


@six.add_metaclass(MetaStoreObject)
@WithRepr
@EqHash('Type', 'Code', 'Message')
@interface.implementer(IPurchaseError)
class PurchaseError(SchemaConfigured, BaseException):
    createDirectFieldProperties(IPurchaseError)

    def __str__(self):
        # pylint: disable=no-member
        return self.Message


def create_purchase_error(message, type_=None, code=None):
    result = PurchaseError(Message=message, Type=type_, Code=code)
    return result


@six.add_metaclass(MetaStoreObject)
@WithRepr
@EqHash('Type', 'Code', 'Message')
@interface.implementer(IRedemptionError)
class RedemptionError(SchemaConfigured):
    createDirectFieldProperties(IRedemptionError)

    def __str__(self):
        # pylint: disable=no-member
        return self.Message


def create_redemption_error(message, type_=None, code=None):
    result = RedemptionError(Message=message, Type=type_, Code=code)
    return result


@six.add_metaclass(MetaStoreObject)
@WithRepr
@EqHash('Type', 'Code', 'Message')
@interface.implementer(IRefundError)
class RefundError(SchemaConfigured, BaseException):
    createDirectFieldProperties(IRefundError)

    def __str__(self):
        # pylint: disable=no-member
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
