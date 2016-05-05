#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Stripe Payment interfaces

.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

from zope import interface

from nti.common.property import alias as _alias

from nti.dataserver.interfaces import IUser

from nti.schema.field import Int
from nti.schema.field import Set
from nti.schema.field import Bool
from nti.schema.field import Object
from nti.schema.field import ValidTextLine

from nti.store.interfaces import IPriceable
from nti.store.interfaces import IPricedItem
from nti.store.interfaces import IPricingError
from nti.store.interfaces import IPurchaseItem
from nti.store.interfaces import IPurchaseError
from nti.store.interfaces import IPurchaseOrder
from nti.store.interfaces import IOperationError 
from nti.store.interfaces import IPaymentProcessor

from nti.store.payments.interfaces import RegisterPurchaseData
from nti.store.payments.interfaces import IRegisterPurchaseData

# stripe marker interfaces

class IStripeCoupon(interface.Interface):
	"""
	marker interface for a stripe coupon
	"""

class IStripeException(interface.Interface):
	"""
	marker interface for a stripe exception
	"""

class IInvalidStripeCoupon(IStripeException):
	"""
	marker interface for an invalid stripe exception
	"""
	
class INoSuchStripeCoupon(IStripeException):
	"""
	marker interface for an no such stripe exception
	"""
	
class IStripeError(interface.Interface):
	"""
	marker interface for a stripe errors
	"""

class IStripeAPIError(IStripeError):
	"""marker interface for a stripe api error"""

class IStripeAPIConnectionError(IStripeError):
	"""
	marker interface for a stripe api connection error
	"""

class IStripeCardError(IStripeError):
	"""
	marker interface for a stripe card errors
	"""

class IStripeInvalidRequestError(IStripeError):
	"""
	marker interface for a stripe invalid request errors
	"""

class IStripeAuthenticationError(IStripeError):
	"""
	marker interface for a stripe authentication errors
	"""

# event interfaces

class IStripeCustomerCreated(interface.Interface):
	user = Object(IUser, title="The user")
	customer_id = ValidTextLine(title="The stripe customer identifier")

@interface.implementer(IStripeCustomerCreated)
class StripeCustomerCreated(object):

	def __init__(self, user, customer_id):
		self.user = user
		self.customer_id = customer_id

class IStripeCustomerDeleted(IStripeCustomerCreated):
	pass

@interface.implementer(IStripeCustomerDeleted)
class StripeCustomerDeleted(StripeCustomerCreated):
	pass

class IRegisterStripeToken(IRegisterPurchaseData):
	token = ValidTextLine(title="The token identifier")

@interface.implementer(IRegisterStripeToken)
class RegisterStripeToken(RegisterPurchaseData):

	def __init__(self, purchase, token_id):
		super(RegisterStripeToken, self).__init__(purchase)
		self.token_id = token_id

	token = _alias('token_id')

class IRegisterStripeCharge(IRegisterPurchaseData):
	charge_id = ValidTextLine(title="The charge identifier")

@interface.implementer(IRegisterStripeCharge)
class RegisterStripeCharge(RegisterPurchaseData):

	def __init__(self, purchase, charge_id):
		super(RegisterStripeCharge, self).__init__(purchase)
		self.charge_id = charge_id

# object interfaces

class IStripeConnectKey(interface.Interface):
	Alias = ValidTextLine(title='Key name or alias', required=True)
	LiveMode = Bool(title="Live mode flag", required=False)
	
	PrivateKey = ValidTextLine(title="The private key", required=True)
	PrivateKey.setTaggedValue('_ext_excluded_out', True)
	
	RefreshToken = ValidTextLine(title="Refresh token", required=False)
	RefreshToken.setTaggedValue('_ext_excluded_out', True)
	
	PublicKey = ValidTextLine(title="The private key", required=False)
	StripeUserID = ValidTextLine(title="String user id", required=False)

class IStripeOperationError(IOperationError):
	HttpStatus = Int(title='HTTP Status', required=False)
	Param = ValidTextLine(title="Optional parameter", required=False)

class IStripePurchaseError(IPurchaseError, IStripeOperationError):
	pass

class IStripePricingError(IPricingError):
	pass

class IStripePurchaseAttempt(interface.Interface):
	ChargeID = ValidTextLine(title='Charge id', required=False)
	TokenID = ValidTextLine(title='Token id', required=False)

class IStripeCustomer(interface.Interface):
	CustomerID = ValidTextLine(title='customer id')
	Charges = Set(value_type=ValidTextLine(title='the charge id'),
				  title='customer stripe charges')

class IStripePaymentProcessor(IPaymentProcessor):

	def create_token(customer_id=None, number=None, exp_month=None, exp_year=None,
					 cvc=None, api_key=None, **kwargs):
		"""
		Create a stripe token
		
		:param customer_id Stripe customer id
		:param number Credit card number
		:param exp_month Expiration month
		:param exp_year Expiration year
		:param cvc CVC number
		"""

	def validate_coupon(coupon):
		"""
		validate the specfied coupon
		"""

	def apply_coupon(amount, coupon=None):
		"""
		apply the specfied coupon to the specfied amount
		"""

	def process_purchase(purchase_id, username, token, expected_amount=None):
		"""
		Process a purchase attempt

		:token Credit Card token
		"""

	def get_payment_charge(purchase_id, username=None):
		"""
		return a payment charge object (or None) for the specified purchase
		"""
		
	def refund_purchase(purchase, amount=None, refund_application_fee=None):
		"""
		Refunds a purchase

		:purchase Transaction/Purchase iden or object
		"""
		
class IStripePriceable(IPriceable):
	Coupon = ValidTextLine(title='the coupon', required=False)

class IStripePurchaseItem(IStripePriceable, IPurchaseItem):
	pass

class IStripePurchaseOrder(IPurchaseOrder):
	Coupon = ValidTextLine(title='the coupon', required=False)

class IStripePricedItem(IPricedItem):
	Coupon = Object(interface.Interface, title='the coupon', required=False)
