#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Stripe customer utilities.

.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope.event import notify

from nti.dataserver.users.interfaces import IUserProfile

from ... import get_user

from .stripe_io import StripeIO
from .stripe_io import get_stripe_customer
from .stripe_io import create_stripe_customer
from .stripe_io import delete_stripe_customer
from .stripe_io import update_stripe_customer

from .interfaces import IStripeCustomer
from .interfaces import StripeCustomerCreated
from .interfaces import StripeCustomerDeleted

def create_customer(user, coupon=None, api_key=None):
	user = get_user(user)
	profile = IUserProfile(user)
	email = getattr(profile, 'email', None)
	description = getattr(profile, 'description', None)
	customer = create_stripe_customer(email=email, description=description,
									  coupon=coupon, api_key=api_key)
	notify(StripeCustomerCreated(user, customer.id))
	return customer
	
def delete_customer(user, api_key=None):
	result = False
	user = get_user(user)
	adapted = IStripeCustomer(user)
	if adapted.customer_id:
		result = delete_stripe_customer(customer_id=adapted.customer_id, api_key=api_key)
		notify(StripeCustomerDeleted(user, adapted.customer_id))
	return result

def update_customer(user, customer=None, coupon=None, api_key=None):
	user = get_user(user)
	profile = IUserProfile(user)
	email = getattr(profile, 'email', None)
	description = getattr(profile, 'description', None)
	adapted = IStripeCustomer(user)
	if adapted.customer_id:
		result = update_stripe_customer(customer=customer or adapted.customer_id,
										email=email,
										coupon=coupon,
										description=description,
										api_key=api_key)
		return result
	return False
	
def get_or_create_customer(user, api_key=None):
	user = get_user(user)
	adapted = IStripeCustomer(user)
	if adapted.customer_id is None:
		customer = create_customer(user, api_key=api_key)
		result = customer.id
	else:
		result = adapted.customer_id
		# get or create the customer so it can be updated later
		customer = 	get_stripe_customer(result, api_key=api_key) or \
					create_customer(user, api_key=api_key)
		# reset the id in case the customer was recreated
		result = adapted.customer_id = customer.id
	return result
		
class StripeCustomer(StripeIO):

	@classmethod
	def create_customer(cls, user, coupon=None, api_key=None):
		result = create_customer(user=user, coupon=coupon, api_key=api_key)
		return result

	@classmethod
	def delete_customer(cls, user, api_key=None):
		result = delete_customer(user=user, api_key=api_key)
		return result

	@classmethod
	def update_customer(cls, user, customer=None, coupon=None, api_key=None):
		result = update_customer(user=user, customer=customer,
								 coupon=coupon, api_key=api_key)
		return result

	@classmethod
	def get_or_create_customer(cls, user, api_key=None):
		result = get_or_create_customer(user=user, api_key=api_key)
		return result

_StripeCustomer = StripeCustomer  # BWC
