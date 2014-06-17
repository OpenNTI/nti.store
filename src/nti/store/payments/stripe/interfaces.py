#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Stripe Payment interfaces

.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

from zope import interface

from nti.dataserver import interfaces as nti_interfaces

from nti.schema.field import Int
from nti.schema.field import Set
from nti.schema.field import Bool
from nti.schema.field import Object
from nti.schema.field import ValidTextLine

from nti.utils.property import alias as _alias

from .. import interfaces as pay_interfaces
from ... import interfaces as store_interfaces

# stripe marker interfaces

class IStripeCoupon(interface.Interface):
	"""marker interface for a stripe coupon"""

class IStripeException(interface.Interface):
	"""marker interface for a stripe exception"""

class IStripeError(interface.Interface):
	"""marker interface for a stripe errors"""

class IStripeAPIError(IStripeError):
	"""marker interface for a stripe api error"""

class IStripeAPIConnectionError(IStripeError):
	"""marker interface for a stripe api connection error"""

class IStripeCardError(IStripeError):
	"""marker interface for a stripe card errors"""

class IStripeInvalidRequestError(IStripeError):
	"""marker interface for a stripe invalid request errors"""

class IStripeAuthenticationError(IStripeError):
	"""marker interface for a stripe authentication errors"""

# event interfaces

class IStripeCustomerCreated(interface.Interface):
	user = Object(nti_interfaces.IUser, title="The user")
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

class IRegisterStripeToken(pay_interfaces.IRegisterPurchaseData):
	token = ValidTextLine(title="The token identifier")

@interface.implementer(IRegisterStripeToken)
class RegisterStripeToken(pay_interfaces.RegisterPurchaseData):

	def __init__(self, purchase, token_id):
		super(RegisterStripeToken, self).__init__(purchase)
		self.token_id = token_id

	token = _alias('token_id')

class IRegisterStripeCharge(pay_interfaces.IRegisterPurchaseData):
	charge_id = ValidTextLine(title="The charge identifier")

@interface.implementer(IRegisterStripeCharge)
class RegisterStripeCharge(pay_interfaces.RegisterPurchaseData):

	def __init__(self, purchase, charge_id):
		super(RegisterStripeCharge, self).__init__(purchase)
		self.charge_id = charge_id

# object interfaces

class IStripeConnectKey(interface.Interface):
	Alias = ValidTextLine(title='Key name or alias', required=True)
	PrivateKey = ValidTextLine(title="The private key", required=True)
	LiveMode = Bool(title="Live mode flag", required=False)
	StripeUserID = ValidTextLine(title="String user id", required=False)
	RefreshToken = ValidTextLine(title="Refresh token", required=False)
	PublicKey = ValidTextLine(title="The private key", required=False)

class IStripePurchaseError(store_interfaces.IPurchaseError):
	HttpStatus = Int(title='HTTP Status', required=False)
	Param = ValidTextLine(title="Optional parameter", required=False)

class IStripePurchaseAttempt(interface.Interface):
	ChargeID = ValidTextLine(title='Charge id', required=False)
	TokenID = ValidTextLine(title='Token id', required=False)

class IStripeCustomer(interface.Interface):
	CustomerID = ValidTextLine(title='customer id')
	Charges = Set(value_type=ValidTextLine(title='the charge id'),
				  title='customer stripe charges')

class IStripePaymentProcessor(store_interfaces.IPaymentProcessor):

	def create_token(customer_id=None, number=None, exp_month=None, exp_year=None,
					 cvc=None, api_key=None, **kwargs):
		"""
		Create a stripe token
		
		:customer_id Stripe customer id
		:number Credit card number
		:exp_month Expiration month
		:exp_year Expiration year
		:cvc CVC number
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
		
	def refund_purchase(trx_id, amount=None, refund_application_fee=None):
		"""
		Returns a purchase

		:trx_id Transaction id
		"""
		
class IStripePriceable(store_interfaces.IPriceable):
	Coupon = ValidTextLine(title='the coupon', required=False)

class IStripePurchaseItem(IStripePriceable, store_interfaces.IPurchaseItem):
	pass

class IStripePurchaseOrder(store_interfaces.IPurchaseOrder):
	Coupon = ValidTextLine(title='the coupon', required=False)

class IStripePricedItem(store_interfaces.IPricedItem):
	Coupon = Object(interface.Interface, title='the coupon', required=False)
