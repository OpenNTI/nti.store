#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component
from zope import interface

from dolmen.builtins import IDict
from dolmen.builtins import IString

from nti.base._compat import unicode_

from nti.store.interfaces import IRefundError
from nti.store.interfaces import IPricingError
from nti.store.interfaces import IPurchaseError
from nti.store.interfaces import IRedemptionError
from nti.store.interfaces import IRefundException
from nti.store.interfaces import IPricingException
from nti.store.interfaces import IPurchaseException
from nti.store.interfaces import IRedemptionException
from nti.store.interfaces import IPurchasableVendorInfo
from nti.store.interfaces import IPurchaseAttemptContext

from nti.store.pricing_error import PricingError

from nti.store.purchasable import DefaultPurchasableVendorInfo

from nti.store.purchase_error import PurchaseError

from nti.store.purchase_attempt import DefaultPurchaseAttemptContext

from nti.store.redemption_error import RedemptionError

from nti.store.refund_error import RefundError


@component.adapter(IDict)
@interface.implementer(IPurchasableVendorInfo)
def _mapping_to_vendorinfo(data):
    return DefaultPurchasableVendorInfo(**data)


@component.adapter(IDict)
@interface.implementer(IPurchaseAttemptContext)
def _mapping_to_purchase_attempt_context(data):
    return DefaultPurchaseAttemptContext(**data)


@component.adapter(IString)
@interface.implementer(IPurchaseError)
def _string_purchase_error(message):
    result = PurchaseError(Type=u"PurchaseError")
    result.Message = unicode_(message or u'')
    return result


@component.adapter(IPurchaseException)
@interface.implementer(IPurchaseError)
def _purchase_exception_adpater(error):
    result = PurchaseError(Type=u"PurchaseError")
    args = getattr(error, 'args', ())
    message = unicode_(' '.join(map(str, args)))
    result.Message = message or 'Unspecified Purchase Exception'
    return result


@component.adapter(IString)
@interface.implementer(IPricingError)
def _string_pricing_error(message):
    result = PricingError(Type=u"PricingError")
    result.Message = unicode_(message or u'')
    return result


@component.adapter(IPricingException)
@interface.implementer(IPricingError)
def _pricing_exception_adpater(error):
    result = PricingError(Type=u"PricingError")
    args = getattr(error, 'args', ())
    message = unicode_(' '.join(map(str, args)))
    result.Message = message or 'Unspecified Pricing Exception'
    return result


@component.adapter(IString)
@interface.implementer(IRefundError)
def _string_refund_error(message):
    result = RefundError(Type=u"RefundError")
    result.Message = unicode_(message or u'')
    return result


@component.adapter(IRefundException)
@interface.implementer(IRefundError)
def _refund_exception_adpater(error):
    result = RefundError(Type=u"RefundError")
    args = getattr(error, 'args', ())
    message = unicode_(' '.join(map(str, args)))
    result.Message = message or 'Unspecified Refund Exception'
    return result


@component.adapter(IString)
@interface.implementer(IRedemptionError)
def _string_redemption_error(message):
    result = RedemptionError(Type=u"RedemptionError")
    result.Message = unicode_(message or u'')
    return result


@component.adapter(IRedemptionException)
@interface.implementer(IRedemptionError)
def _redemption_exception_adpater(error):
    result = RedemptionError(Type=u"RedemptionError")
    args = getattr(error, 'args', ())
    message = unicode_(' '.join(map(str, args)))
    result.Message = message or 'Unspecified Redemption Exception'
    return result
