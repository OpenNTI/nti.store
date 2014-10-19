#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Stripe purchase functionalilty.

.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import six
import sys
import math
from functools import partial

from stripe import InvalidRequestError

from zope import component
from zope.event import notify

from nti.dataserver.interfaces import IDataserverTransactionRunner

from .... import PurchaseException

from ....interfaces import PurchaseAttemptFailed
from ....interfaces import PurchaseAttemptStarted
from ....interfaces import PurchaseAttemptSuccessful

from ....store import get_purchase_attempt

from ..stripe_io import create_charge
from ..stripe_customer import StripeCustomer
from ..stripe_customer import update_customer
from ..stripe_customer import get_or_create_customer

from ..utils import create_payment_charge
from ..utils import adapt_to_purchase_error
from ..utils import encode_charge_description

from ..interfaces import RegisterStripeToken
from ..interfaces import RegisterStripeCharge
from ..interfaces import IStripePurchaseAttempt

from .coupon import CouponProcessor
from .pricing import price_purchase
from .pricing import PricingProcessor

def get_transaction_runner():
	result = component.getUtility(IDataserverTransactionRunner)
	return result

def _start_purchase(purchase_id, username=None):
	purchase = get_purchase_attempt(purchase_id, username)
	if purchase is None:
		raise PurchaseException("Could not find purchase attempt %s" % purchase_id)

	if not purchase.is_pending():
		notify(PurchaseAttemptStarted(purchase))

	# price purchase
	pricing = price_purchase(purchase)
	return pricing
		
def _register_stripe_token_and_user(purchase_id, token, username=None, api_key=None):
	purchase = get_purchase_attempt(purchase_id, username)
	if not purchase.has_completed():
		notify(RegisterStripeToken(purchase, token))
		if username:
			logger.info('Getting/Creating Stripe Customer for %s', username)
			customer_id = get_or_create_customer(username, api_key=api_key)
			return customer_id
	return None
	
def _do_stripe_purchase(purchase_id, cents_amount, currency, card,
						username=None, application_fee=None, customer_id=None,
						api_key=None):
	charge = None
	purchase = get_purchase_attempt(purchase_id, username)
	if purchase.is_pending():
		# charge card, user description for tracking purposes
		context = purchase.Context
		descid = encode_charge_description(purchase_id=purchase_id, 
										   username=username,
										   customer_id=customer_id,
										   context=context)
		logger.info('Creating stripe charge for %s', purchase_id)
		charge = create_charge(	cents_amount, currency=currency,
								card=card, description=descid,
								application_fee=application_fee,
								api_key=api_key)
	return charge

def _register_charge_notify(purchase_id, charge, username=None,
							pricing=None, request=None, api_key=None):
	
	purchase = get_purchase_attempt(purchase_id, username)
	if not purchase.is_pending():
		return

	notify(RegisterStripeCharge(purchase, charge.id))
	
	if charge.paid:
		# notify success
		purchase.Pricing = pricing
		payment_charge = create_payment_charge(charge)
		notify(PurchaseAttemptSuccessful(purchase, payment_charge, request))

		# update coupon. In case there is an error updating the coupon
		# (e.g. max redemptions reached) the we will still the transaction go.
		# Log error and this must be check manually
		coupon = purchase.Order.Coupon
		if coupon is not None and username:
			try:
				update_customer(username, coupon=coupon, api_key=api_key)
			except StandardError:
				logger.exception("Exception while updating the user " +
								 "coupon. The charge is still valid")

def _fail_purchase(purchase_id, error, username=None):
	purchase = get_purchase_attempt(purchase_id, username)
	if purchase is not None:
		notify(PurchaseAttemptFailed(purchase, error))
			
class PurchaseProcessor(StripeCustomer, CouponProcessor, PricingProcessor):

	def process_purchase(self, purchase_id, token, username=None, expected_amount=None,
						 api_key=None, request=None, site_names=None):
		"""
		Executes the process purchase.
		This function may be called in a greenlet
		(which cannot be run within a transaction runner);
		the request should be established when it is called.
		"""

		# prepare transaction runner
		transaction_runner = get_transaction_runner()
		transaction_runner = partial(transaction_runner, site_names=site_names)

		start_purchase = partial(_start_purchase, 
								 purchase_id=purchase_id,
								 username=username)

		register_stripe_token_and_user = partial(_register_stripe_token_and_user, 
												 purchase_id=purchase_id,
								 				 username=username,
								 				 token=token,
								 				 api_key=api_key)
		try:
			# start the purchase and price trx
			pricing = transaction_runner(start_purchase)
			
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

			# create a stripe customer
			customer_id = transaction_runner(register_stripe_token_and_user)

			# get price amount in cents
			cents_amount = int(amount * 100.0)
			application_fee = int(application_fee * 100.0) if application_fee else None

			do_stripe_purchase =  partial(_do_stripe_purchase, 
										  card=token,
										  username=username,
										  currency=currency,
										  purchase_id=purchase_id,
										  customer_id=customer_id,
										  cents_amount=cents_amount,
										  application_fee=application_fee,
										  api_key=api_key)
			charge = transaction_runner(do_stripe_purchase)

			if charge is not None:
				register_charge_notify = partial(_register_charge_notify, 
												 purchase_id=purchase_id,
												 username=username,
												 charge=charge,
												 pricing=pricing,
												 request=request,
												 api_key=api_key)
				transaction_runner(register_charge_notify)

			# return charge id
			return charge.id if charge is not None else None
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
