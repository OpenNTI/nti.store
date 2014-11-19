#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Stripe refund functionalilty.

.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import six
import time
from datetime import date

from zope.event import notify

from .... import RefundException

from ....store import get_purchase_attempt
from ....store import get_purchase_by_code
from ....interfaces import IPurchaseAttempt
from ....interfaces import PurchaseAttemptRefunded

from ..utils import create_payment_charge

from ..interfaces import RegisterStripeCharge
from ..interfaces import IStripePurchaseAttempt

from .base import BaseProcessor

def find_purchase(key):
	try:
		purchase = get_purchase_by_code(key)
	except Exception:
		purchase = get_purchase_attempt(key)
	return purchase

class RefundProcessor(BaseProcessor):

	def refund_purchase(self, purchase, amount=None, refund_application_fee=None,
						api_key=None, request=None):
		"""
		Refunds to a purchase attempt
		"""

		if amount is not None and amount <= 0:
			raise RefundException('Invalid refund amount')

		if isinstance(purchase, six.string_types):
			purchase = find_purchase(purchase)
			if purchase is None:
				raise RefundException('Purchase attempt could not be found')
		
		assert IPurchaseAttempt.providedBy(purchase)
		
		if not purchase.has_succeeded():
			raise RefundException('Purchase did not succeeded')
		elif purchase.is_refunded():
			logger.warn('Purchase attempt has already been refunded')
			return False

		purchase_id = purchase.id
		api_key = api_key or self.get_api_key(purchase)
		if api_key is None:
			logger.error('Could not get a valid provider for purchase %r', purchase_id)
			return False

		pricing = purchase.Pricing
		if amount is not None and amount > pricing.TotalPurchasePrice:
			logger.warn('Refund amount is greater than the charge amount. Adjusting')
			amount = pricing.TotalPurchasePrice
			
		application_fee = pricing.TotalPurchaseFee
		if refund_application_fee is None:
			if application_fee:
				refund_application_fee = True
			else:
				refund_application_fee = False

		charge = None
		sp = IStripePurchaseAttempt(purchase)
		if sp.ChargeID:
			charge = self.get_stripe_charge(sp.ChargeID, api_key=api_key)
		else:
			start_time = time.mktime(date.fromtimestamp(purchase.StartTime).timetuple())
			charges = self.get_charges(purchase_id=purchase_id, start_time=start_time,
									   api_key=api_key)
			if charges:
				charge = charges[0]  # get first
				# re-register for future use
				notify(RegisterStripeCharge(purchase, charge.id))
			
		if charge:
			cents_amount = int(amount * 100.0) if amount is not None else None
			logger.debug('Refunding %s...', purchase_id)
			if not charge.refunded:
				charge.refund(amount=cents_amount,
							  refund_application_fee=refund_application_fee)
			else:
				logger.warn('Stripe charge already refunded')

			notify(PurchaseAttemptRefunded(purchase, 
										   create_payment_charge(charge),
										   request))
		else:
			raise RefundException('Stripe charge not found')

		return charge
