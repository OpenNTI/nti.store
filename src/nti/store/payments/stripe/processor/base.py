#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from requests.structures import CaseInsensitiveDict

from zope import component

from nti.store.payments.stripe import STRIPE

from nti.store.payments.stripe.stripe_io import StripeIO
from nti.store.payments.stripe.stripe_io import get_stripe_charges
from nti.store.payments.stripe.stripe_io import create_stripe_token

from nti.store.payments.stripe.interfaces import IStripeConnectKey

from nti.store.purchase_attempt import get_providers

def get_api_key(purchase):
	providers = get_providers(purchase)
	provider = providers[0] if providers else u''  # pick first provider
	stripe_key = component.queryUtility(IStripeConnectKey, provider)
	result = stripe_key.PrivateKey if stripe_key else None
	return result
get_api_key_from_purchase = get_api_key # alias

def get_charges(purchase_id=None, username=None, customer=None,
				start_time=None, end_time=None, api_key=None):
	result = []
	for charge in get_stripe_charges(start_time=start_time,
									 end_time=end_time,
									 api_key=api_key):
		
		description = charge.description
		metadata = CaseInsensitiveDict(charge.metadata or {})
		if  	(purchase_id and metadata.get('PurchaseID') == purchase_id) \
			or 	(customer and metadata.get('CustomerID') == customer) \
			or 	(username and metadata.get('Username') == username):
			result.append(charge)
		elif description: ## legacy
			if  	(purchase_id and purchase_id in description) \
				or 	(username and username in description) \
				or 	(customer and customer in description):
				result.append(charge)
	return result

def create_card_token(customer_id=None, number=None, exp_month=None,
					  exp_year=None, cvc=None, api_key=None, **kwargs):
	token = create_stripe_token(customer_id, number, exp_month, exp_year, cvc, 
								api_key, **kwargs)
	return token.id

class BaseProcessor(StripeIO):

	name = STRIPE

	@classmethod
	def get_api_key(cls, purchase):
		result = get_api_key(purchase)
		return result
	get_api_key_from_purchase = get_api_key # alias
	
	@classmethod
	def get_charges(cls, purchase_id=None, username=None, customer=None,
					start_time=None, end_time=None, api_key=None):
		result = get_charges(purchase_id=purchase_id, username=username,
							 customer=customer, start_time=start_time,
							 end_time=end_time, api_key=api_key)
		return result

	@classmethod
	def create_card_token(cls, customer_id=None, number=None, exp_month=None,
						  exp_year=None, cvc=None, api_key=None, **kwargs):
		result = create_card_token(	customer_id=customer_id, number=number, 
									exp_month=exp_month, exp_year=exp_year,
									cvc=cvc, api_key=api_key, **kwargs)
		return result
