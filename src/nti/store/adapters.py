#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import component
from zope import interface

from nti.base._compat import text_

from nti.base.interfaces import IDict
from nti.base.interfaces import IString

from nti.site.interfaces import IHostPolicyFolder

from nti.store.interfaces import IPurchasable
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

from nti.store.model import RefundError
from nti.store.model import PricingError
from nti.store.model import PurchaseError
from nti.store.model import RedemptionError

from nti.store.purchasable import DefaultPurchasableVendorInfo

from nti.store.purchase_attempt import DefaultPurchaseAttemptContext

from nti.traversal.traversal import find_interface

logger = __import__('logging').getLogger(__name__)


@component.adapter(IPurchasable)
@interface.implementer(IHostPolicyFolder)
def purchasable_to_site(context):
    return find_interface(context, IHostPolicyFolder, strict=False)


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
    result.Message = text_(message or u'')
    return result


@component.adapter(IPurchaseException)
@interface.implementer(IPurchaseError)
def _purchase_exception_adpater(error):
    result = PurchaseError(Type=u"PurchaseError")
    args = getattr(error, 'args', ())
    message = u' '.join(map(str, args))
    result.Message = message or u'Unspecified Purchase Exception'
    return result


@component.adapter(IString)
@interface.implementer(IPricingError)
def _string_pricing_error(message):
    result = PricingError(Type=u"PricingError")
    result.Message = text_(message or u'')
    return result


@component.adapter(IPricingException)
@interface.implementer(IPricingError)
def _pricing_exception_adpater(error):
    result = PricingError(Type=u"PricingError")
    args = getattr(error, 'args', ())
    message = u' '.join(map(str, args))
    result.Message = message or u'Unspecified Pricing Exception'
    return result


@component.adapter(IString)
@interface.implementer(IRefundError)
def _string_refund_error(message):
    result = RefundError(Type=u"RefundError")
    result.Message = text_(message or u'')
    return result


@component.adapter(IRefundException)
@interface.implementer(IRefundError)
def _refund_exception_adpater(error):
    result = RefundError(Type=u"RefundError")
    args = getattr(error, 'args', ())
    message = u' '.join(map(str, args))
    result.Message = message or u'Unspecified Refund Exception'
    return result


@component.adapter(IString)
@interface.implementer(IRedemptionError)
def _string_redemption_error(message):
    result = RedemptionError(Type=u"RedemptionError")
    result.Message = text_(message or u'')
    return result


@component.adapter(IRedemptionException)
@interface.implementer(IRedemptionError)
def _redemption_exception_adpater(error):
    result = RedemptionError(Type=u"RedemptionError")
    args = getattr(error, 'args', ())
    message = u' '.join(map(str, args))
    result.Message = message or u'Unspecified Redemption Exception'
    return result
