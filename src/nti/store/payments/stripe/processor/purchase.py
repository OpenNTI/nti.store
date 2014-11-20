#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Stripe purchase functionalilty.

.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from .... import MessageFactory as _

import six
import sys
import math
from functools import partial

from stripe import InvalidRequestError

from zope import component
from zope.event import notify

from nti.dataserver.interfaces import IDataserverTransactionRunner

from nti.site.site import find_site_components

from .... import get_user
from .... import PurchaseException

from ....store import get_purchase_attempt

from ....interfaces import PurchaseAttemptFailed
from ....interfaces import PurchaseAttemptStarted
from ....interfaces import PurchaseAttemptSuccessful

from ..stripe_io import create_charge
from ..stripe_io import update_charge
from ..stripe_customer import StripeCustomer
from ..stripe_customer import create_customer

from ..utils import get_charge_metata
from ..utils import create_payment_charge
from ..utils import adapt_to_purchase_error
from ..utils import encode_charge_description

from ..interfaces import IStripeCustomer
from ..interfaces import RegisterStripeToken
from ..interfaces import RegisterStripeCharge
from ..interfaces import IStripePurchaseAttempt

from .coupon import CouponProcessor

from .pricing import price_order
from .pricing import PricingProcessor

def get_transaction_runner():
	result = component.getUtility(IDataserverTransactionRunner)
	return result

def _start_purchase(purchase_id, token, username=None):
	purchase = get_purchase_attempt(purchase_id, username)
	if purchase is None:
		raise PurchaseException("Could not find purchase attempt %s" % purchase_id)

	if not purchase.is_pending():
		notify(PurchaseAttemptStarted(purchase))
		notify(RegisterStripeToken(purchase, token))

	customer_id = None
	if username:
		user = get_user(username)
		adapted = IStripeCustomer(user, None)
		customer_id = adapted.customer_id if adapted else None
		
	context = purchase.Context
	order = purchase.Order.copy() # make a copy of the order
	metadata = get_charge_metata(purchase_id, username=username, 
								 context=context, customer_id=customer_id)
	return (order, metadata, customer_id)

def _execute_stripe_charge(	purchase_id, cents_amount, currency, card,
							application_fee=None, customer_id=None, 
							metadata=None, api_key=None):
	logger.info('Creating stripe charge for %s', purchase_id)
	metadata = metadata or {}
	charge = create_charge(	cents_amount, currency=currency,
							card=card, metadata=metadata,
							customer_id=customer_id,
							application_fee=application_fee,
							api_key=api_key,
							description=encode_charge_description(metadata=metadata))
	return charge

def _register_charge_notify(purchase_id, charge, username=None,
							pricing=None, request=None, api_key=None):
	purchase = get_purchase_attempt(purchase_id, username)
	if not purchase.is_pending():
		return False
	
	## register the charge id w/ the purchase and creator
	notify(RegisterStripeCharge(purchase, charge.id))
	
	## check charge
	if charge.paid:
		result = True
		purchase.Pricing = pricing
		payment_charge = create_payment_charge(charge)
		notify(PurchaseAttemptSuccessful(purchase, payment_charge, request))
	else:
		result = False
		message = charge.failure_message 
		notify(PurchaseAttemptFailed(purchase, adapt_to_purchase_error(message)))
	return result

def _fail_purchase(purchase_id, error, username=None):
	purchase = get_purchase_attempt(purchase_id, username)
	if purchase is not None:
		notify(PurchaseAttemptFailed(purchase, error))
	
def _get_purchase(purchase_id, username=None):
	purchase = get_purchase_attempt(purchase_id, username)
	return purchase
					
class PurchaseProcessor(StripeCustomer, CouponProcessor, PricingProcessor):

	def _create_customer(self, transaction_runner, user, api_key=None):
		try:
			creator_func = partial(create_customer, user=user, api_key=api_key)
			result = transaction_runner(creator_func)
			return result
		except Exception as e:
			logger.error("Could not create stripe customer %s. %s", user, e)
		return None
	
	def _update_charge(self, charge, customer_id, metadata=None, api_key=None):
		try:
			metadata = metadata or {}
			metadata['CustomerID'] = customer_id
			description = encode_charge_description(metadata=metadata)
			update_charge(charge, metadata=metadata, description=description,
						  api_key=api_key)
		except Exception as e:
			logger.error("Could not update stripe charge %s. %s", charge.id, e)
		return None

	def _update_customer(self, transaction_runner, username, customer, coupon, api_key=None):
		updater_func = partial(self.update_customer, user=username, customer=customer,
							   coupon=coupon, api_key=api_key)
		try:
			result = transaction_runner(updater_func)
			return result
		except Exception:
			logger.exception("Exception while updating the user coupon.")
					
	def _post_purchase(self, transaction_runner, purchase_id, charge, 
					   metadata=None, customer_id=None, username=None, api_key=None):
		if not username:
			return
		
		if not customer_id:
			customer = self._create_customer(transaction_runner, 
											 username, 
											 api_key=api_key)
			customer_id = customer.id if customer is not None else None
			if customer_id:
				self._update_charge(charge, customer_id, metadata, api_key)

		getter_func = partial(_get_purchase, purchase_id=purchase_id, username=username)
		purchase = transaction_runner(getter_func)
		if customer_id and purchase is not None:
			# update coupon. In case there is an error updating the coupon
			# (e.g. max redemptions reached) Log error and this must be check manually
			coupon = purchase.Order.Coupon
			if coupon is not None:
				self._update_customer(transaction_runner, username=username,
									  customer=customer_id, coupon=coupon, 
									  api_key=api_key)

	def process_purchase(self, purchase_id, token, username=None, expected_amount=None,
						 api_key=None, request=None, site_names=None):
		"""
		Executes the process purchase.
		This function may be called in a greenlet
		(which cannot be run within a transaction runner);
		the request should be established when it is called.
		"""
		charge = None
		success = False
		site_names = site_names or ()
		
		# prepare transaction runner
		transaction_runner = get_transaction_runner()
		transaction_runner = partial(transaction_runner, 
									 site_names=site_names,
									 retries=3, sleep=0.2)

		start_purchase = partial(_start_purchase, 
								 purchase_id=purchase_id,
								 username=username,
								 token=token)
		try:
			## start the purchase. 
			## We notify purchase has started and 
			## return the order to price, charge metatada, stripe customer id
			order, metadata, customer_id = transaction_runner(start_purchase)
			
			## price the purchasable order
			## this is done outside a DS transaction in case
			## we need to get a stripe coupon. make sure 
			## we get the right site component
			registry = find_site_components(site_names) 
			registry = component if registry is None else registry
			pricing = price_order(order, registry=registry)
			
			## check priced amount w/ expected amount
			currency = pricing.Currency
			amount = pricing.TotalPurchasePrice
			application_fee = pricing.TotalPurchaseFee \
							  if pricing.TotalPurchaseFee else None
			if 	expected_amount is not None and \
				not math.fabs(expected_amount - amount) <= 0.05:
				logger.error("Purchase order amount %.2f did not match the " +
							 "expected amount %.2f", amount, expected_amount)
				raise PurchaseException("Purchase order amount did not match the "
										"expected amount")

			## get priced amount in cents as expected by stripe
			cents_amount = int(amount * 100.0)
			application_fee = int(application_fee * 100.0) if application_fee else None
							
			## execute stripe charge outside a DS transaction
			charge = _execute_stripe_charge(card=token,
											currency=currency,
											metadata=metadata,
											customer_id=customer_id,
											purchase_id=purchase_id, 
											cents_amount=cents_amount,
											application_fee=application_fee,
											api_key=api_key)
			
			if charge is not None:
				register_charge_notify = partial(_register_charge_notify, 
												 purchase_id=purchase_id,
												 username=username,
												 charge=charge,
												 pricing=pricing,
												 request=request,
												 api_key=api_key)
				success = transaction_runner(register_charge_notify)
				
			else:
				error = _("Could not execute purchase charge at Stripe")
				error = adapt_to_purchase_error(error)
				fail_purchase = partial(_fail_purchase, 
										purchase_id=purchase_id,
										username=username,
										error=error)
				transaction_runner(fail_purchase)
		except Exception as e:
			logger.exception("Cannot complete process purchase for '%s'", purchase_id)
			
			t, v, tb = sys.exc_info()
			error = adapt_to_purchase_error(e)
			fail_purchase = partial(_fail_purchase, 
									purchase_id=purchase_id,
									username=username,
									error=error)
			transaction_runner(fail_purchase)
			
			# report exception
			raise t, v, tb
		
		## now we can do post purchase registration that is
		## independent of the purchase
		if success:
			self._post_purchase(transaction_runner, 
								charge=charge,
								api_key=api_key,
								metadata=metadata,
								username=username, 
								purchase_id=purchase_id,
								customer_id=customer_id)

		# return charge id
		return charge.id if charge is not None else None

	def get_payment_charge(self, purchase, username=None, api_key=None):
		purchase_id = purchase # save original
		if isinstance(purchase, six.string_types):
			purchase = get_purchase_attempt(purchase, username)

		if purchase is None:
			raise PurchaseException("Could not find purchase attempt %s" % purchase_id)

		api_key = api_key or self.get_api_key(purchase)
		if not api_key:
			raise PurchaseException("Could not find a stripe key for %s" % purchase_id)

		spurchase = IStripePurchaseAttempt(purchase)
		charge_id = spurchase.ChargeID
		try:
			if charge_id:
				charge = self.get_stripe_charge(charge_id, api_key=api_key)
			else:
				charge = None
			result = create_payment_charge(charge) if charge else None
		except InvalidRequestError:
			result = None
		return result
