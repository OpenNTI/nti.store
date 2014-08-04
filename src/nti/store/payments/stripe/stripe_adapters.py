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
from zope.container.contained import Contained
from zope.annotation import factory as an_factory

from persistent import Persistent

from nti.dataserver.interfaces import IUser

from nti.utils.property import alias

from .utils import makenone

from . import StripePurchaseError

from .interfaces import IStripeError
from .interfaces import IStripeAPIError
from .interfaces import IStripeCustomer
from .interfaces import IStripeCardError
from .interfaces import IStripeException
from .interfaces import IStripePurchaseError
from .interfaces import IStripePurchaseAttempt
from .interfaces import IStripeAPIConnectionError
from .interfaces import IStripeAuthenticationError
from .interfaces import IStripeInvalidRequestError

from ...interfaces import IPurchaseAttempt

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
	result = StripePurchaseError(Type=u"Error")
	result.Message = unicode(message or u'')
	return result

@component.adapter(IStripeException)
@interface.implementer(IStripePurchaseError)
def stripe_exception_adpater(error):
	result = StripePurchaseError(Type=u"Exception")
	args = getattr(error, 'args', ())
	message = unicode(' '.join(map(str, args)))
	result.Message = message or 'Unspecified Stripe Exception'
	return result

@component.adapter(IStripeError)
@interface.implementer(IStripePurchaseError)
def stripe_error_adpater(error):
	result = StripePurchaseError(Type=u"Error")
	result.HttpStatus = getattr(error, 'http_status', None)
	args = getattr(error, 'args', ())
	message = makenone(error.message) or ' '.join(map(str, args))
	result.Message = unicode(message or 'Unspecified Stripe Error')
	return result

@component.adapter(IStripeAPIError)
@interface.implementer(IStripePurchaseError)
def stripe_api_error_adpater(error):
	result = stripe_error_adpater(error)
	result.Type = u"APIError"
	return result

@component.adapter(IStripeAPIConnectionError)
@interface.implementer(IStripePurchaseError)
def stripe_api_connection_error_adpater(error):
	result = stripe_error_adpater(error)
	result.Type = "APIConnectionError"
	return result

@component.adapter(IStripeCardError)
@interface.implementer(IStripePurchaseError)
def stripe_card_error_adpater(error):
	result = stripe_error_adpater(error)
	result.Type = u"CardError"
	result.Code = makenone(getattr(error, 'code', None))
	result.Param = makenone(getattr(error, 'param', None))
	return result

@component.adapter(IStripeCardError)
@interface.implementer(IStripeInvalidRequestError)
def stripe_invalid_request_error_adpater(error):
	result = stripe_error_adpater(error)
	result.Type = u"InvalidRequestError"
	return result

@component.adapter(IStripeAuthenticationError)
@interface.implementer(IStripePurchaseError)
def stripe_auth_error_adpater(error):
	result = stripe_error_adpater(error)
	result.Type = u"AuthenticationError"
	return result
