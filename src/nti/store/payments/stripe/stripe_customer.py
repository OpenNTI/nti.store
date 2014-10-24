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
from .stripe_io import create_stripe_customer
from .stripe_io import delete_stripe_customer
from .stripe_io import update_stripe_customer

from .interfaces import IStripeCustomer
from .interfaces import StripeCustomerCreated
from .interfaces import StripeCustomerDeleted

def get_customer_data(user):
	result = None
	user = get_user(user)
	if user is not None:
		profile = IUserProfile(user)
		result = {
			'email':getattr(profile, 'email', None),
			'description':getattr(profile, 'description', None) 
		}
	return result

def create_customer(user, coupon=None, api_key=None):
	user = get_user(user)
	if user is not None:
		params = get_customer_data(user)
		params['coupon'] = coupon
		params['api_key'] = api_key
		customer = create_stripe_customer(**params)
		notify(StripeCustomerCreated(user, customer.id))
		return customer
	return None
	
def delete_customer(user, api_key=None):
	result = False
	user = get_user(user)
	if user is not None:
		adapted = IStripeCustomer(user)
		customer_id = adapted.customer_id
		if customer_id:
			result = delete_stripe_customer(customer_id=customer_id, api_key=api_key)
			notify(StripeCustomerDeleted(user, adapted.customer_id))
		return result
	return False

def update_customer(user, customer=None, coupon=None, api_key=None):
	user = get_user(user)
	if user is not None:
		profile = IUserProfile(user)
		adapted = IStripeCustomer(user)
		email = getattr(profile, 'email', None)
		description = getattr(profile, 'description', None)
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
	if user is not None:
		adapted = IStripeCustomer(user)
		if adapted.customer_id is None:
			customer = create_customer(user, api_key=api_key)
			result = customer.id
		else:
			result = adapted.customer_id
		return result
	return None
		
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
