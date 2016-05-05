#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Stripe purchase adapters.

.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import BTrees

from zope import component
from zope import interface

from zope.annotation import factory as an_factory

from zope.container.contained import Contained

from persistent import Persistent

from nti.common.property import alias

from nti.dataserver.interfaces import IUser

from nti.store.interfaces import IPurchaseAttempt

from nti.store.payments.stripe import StripePurchaseError
from nti.store.payments.stripe import StripeOperationError

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

from nti.store.payments.stripe.utils import makenone

@component.adapter(IUser)
@interface.implementer(IStripeCustomer)
class _StripeCustomer(Contained, Persistent):

	family = BTrees.family64

	CustomerID = None

	def __init__(self):
		self.Charges = self.family.OO.OOTreeSet()

	@property
	def id(self):
		return self.CustomerID

	def __contains__(self, charge):
		return  charge in self.Charges

	charges = alias('Charges')
	customer_id = alias('CustomerID')

_StripeCustomerFactory = an_factory(_StripeCustomer)

@component.adapter(IPurchaseAttempt)
@interface.implementer(IStripePurchaseAttempt)
class _StripePurchaseAttempt(Contained, Persistent):

	TokenID = None
	ChargeID = None

	@property
	def purchase(self):
		return self.__parent__

	token_id = alias('TokenID')
	charge_id = alias('ChargeID')

_StripePurchase = _StripePurchaseAttempt  # BWC
_StripePurchaseAttemptFactory = an_factory(_StripePurchaseAttempt)

@component.adapter(basestring)
@interface.implementer(IStripePurchaseError)
def _string_purchase_error(message):
	result = StripePurchaseError(Type=u"PurchaseError")
	result.Message = unicode(message or u'')
	return result

@component.adapter(IStripeException)
@interface.implementer(IStripePurchaseError)
def stripe_exception_adpater(error):
	result = StripePurchaseError(Type=u"PurchaseError")
	args = getattr(error, 'args', ())
	message = unicode(' '.join(map(str, args)))
	result.Message = message or 'Unspecified Stripe Purchase Exception'
	return result

@component.adapter(INoSuchStripeCoupon)
@interface.implementer(IStripePurchaseError)
def no_such_stripe_coupon_adpater(error):
	result = stripe_exception_adpater(error)
	result.Message = u'No such Stripe coupon'
	return result

@component.adapter(IInvalidStripeCoupon)
@interface.implementer(IStripePurchaseError)
def invalid_stripe_coupon_adpater(error):
	result = stripe_exception_adpater(error)
	result.Message = u'Invalid Stripe coupon'
	return result

def stripe_operation_adpater(error, Type, clazz=StripeOperationError):
	result = clazz(Type=Type)
	args = getattr(error, 'args', ())
	result.HttpStatus = getattr(error, 'http_status', None)
	message = makenone(error.message) or ' '.join(map(str, args))
	result.Message = unicode(message or 'Unspecified Stripe Error')
	return result

@component.adapter(basestring)
@interface.implementer(IStripeOperationError)
def _string_operation_error(message):
	result = StripeOperationError(Type=u"OperationError")
	result.Message = unicode(message or u'')
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
