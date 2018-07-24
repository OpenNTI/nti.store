#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Stripe purchase adapters.

.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import BTrees

from zope import component
from zope import interface

from zope.annotation import factory as an_factory

from zope.container.contained import Contained

from persistent import Persistent

from nti.base._compat import text_

from nti.base.interfaces import IBasestring

from nti.dataserver.interfaces import IUser

from nti.property.property import alias

from nti.store import MessageFactory as _

from nti.store.interfaces import IPurchaseAttempt

from nti.store.payments.stripe.interfaces import STRIPE_CUSTOMER_KEY
from nti.store.payments.stripe.interfaces import STRIPE_PURCHASE_KEY

from nti.store.payments.stripe.interfaces import IStripeError
from nti.store.payments.stripe.interfaces import IStripeAPIError
from nti.store.payments.stripe.interfaces import IStripeCustomer
from nti.store.payments.stripe.interfaces import IStripeCardError
from nti.store.payments.stripe.interfaces import IStripeException
from nti.store.payments.stripe.interfaces import INoSuchStripeCoupon
from nti.store.payments.stripe.interfaces import IInvalidStripeCoupon
from nti.store.payments.stripe.interfaces import IStripePurchaseError
from nti.store.payments.stripe.interfaces import IStripeOperationError
from nti.store.payments.stripe.interfaces import IStripePurchaseAttempt
from nti.store.payments.stripe.interfaces import IStripeAPIConnectionError
from nti.store.payments.stripe.interfaces import IStripeAuthenticationError
from nti.store.payments.stripe.interfaces import IStripeInvalidRequestError

from nti.store.payments.stripe.model import StripePurchaseError
from nti.store.payments.stripe.model import StripeOperationError

from nti.store.payments.stripe.utils import makenone


@component.adapter(IUser)
@interface.implementer(IStripeCustomer)
class _StripeCustomer(Persistent, Contained):

    family = BTrees.family64

    CustomerID = None
    
    charges = alias('Charges')
    customer_id = alias('CustomerID')
    
    def __init__(self):
        self.Charges = self.family.OO.OOTreeSet()

    @property
    def id(self):
        return self.CustomerID

    def __contains__(self, charge):
        return charge in self.Charges

_StripeCustomerFactory = an_factory(_StripeCustomer, 
                                    STRIPE_CUSTOMER_KEY)


@component.adapter(IPurchaseAttempt)
@interface.implementer(IStripePurchaseAttempt)
class _StripePurchaseAttempt(Persistent, Contained):

    TokenID = None
    ChargeID = None

    token_id = alias('TokenID')
    charge_id = alias('ChargeID')

    @property
    def purchase(self):
        return self.__parent__
    

_StripePurchaseAttemptFactory = an_factory(_StripePurchaseAttempt,
                                           STRIPE_PURCHASE_KEY)

import zope.deferredimport
zope.deferredimport.initialize()
zope.deferredimport.deprecated(
    "Import from _StripePurchaseAttempt instead",
    _StripePurchase='nti.store.payments.stripe.adapters._StripePurchaseAttempt')


@component.adapter(IBasestring)
@interface.implementer(IStripePurchaseError)
def _string_purchase_error(message):
    result = StripePurchaseError(Type=u"PurchaseError")
    result.Message = text_(message or u'')
    return result


@component.adapter(IStripeException)
@interface.implementer(IStripePurchaseError)
def stripe_exception_adpater(error):
    result = StripePurchaseError(Type=u"PurchaseError")
    args = getattr(error, 'args', ())
    message = u' '.join(map(str, args))
    result.Message = message or _(u'Unspecified Stripe Purchase Exception')
    return result


@component.adapter(INoSuchStripeCoupon)
@interface.implementer(IStripePurchaseError)
def no_such_stripe_coupon_adpater(error):
    result = stripe_exception_adpater(error)
    result.Message = _(u'No such Stripe coupon')
    return result


@component.adapter(IInvalidStripeCoupon)
@interface.implementer(IStripePurchaseError)
def invalid_stripe_coupon_adpater(error):
    result = stripe_exception_adpater(error)
    result.Message = _(u'Invalid Stripe coupon')
    return result


def stripe_operation_adpater(error, Type, clazz=StripeOperationError):
    result = clazz(Type=Type)
    args = getattr(error, 'args', ())
    result.HttpStatus = getattr(error, 'http_status', None)
    message = makenone(error.message) or u' '.join(map(str, args))
    result.Message = message or _(u'Unspecified Stripe Error')
    return result


@component.adapter(IBasestring)
@interface.implementer(IStripeOperationError)
def _string_operation_error(message):
    result = StripeOperationError(Type=u"OperationError")
    result.Message = text_(message or u'')
    return result


@component.adapter(IStripeAPIError)
@interface.implementer(IStripeOperationError)
def stripe_api_error_adpater(error):
    result = stripe_operation_adpater(error, Type=u"APIError")
    return result


@component.adapter(IStripeAPIConnectionError)
@interface.implementer(IStripeOperationError)
def stripe_api_connection_error_adpater(error):
    result = stripe_operation_adpater(error, Type=u"APIConnectionError")
    return result


@component.adapter(IStripeCardError)
@interface.implementer(IStripeOperationError)
def stripe_card_error_adpater(error):
    result = stripe_operation_adpater(error, Type=u"CardError")
    result.Code = makenone(getattr(error, 'code', None))
    result.Param = makenone(getattr(error, 'param', None))
    return result


@component.adapter(IStripeInvalidRequestError)
@interface.implementer(IStripeOperationError)
def stripe_invalid_request_error_adpater(error):
    result = stripe_operation_adpater(error, Type=u"InvalidRequestError")
    result.Code = makenone(getattr(error, 'code', None))
    return result


@component.adapter(IStripeAuthenticationError)
@interface.implementer(IStripeOperationError)
def stripe_auth_error_adpater(error):
    result = stripe_operation_adpater(error, Type=u"AuthenticationError")
    return result


@component.adapter(IStripeError)
@interface.implementer(IStripeOperationError)
def stripe_error_adpater(error):
    result = stripe_operation_adpater(error, Type=u"StripeError")
    return result
