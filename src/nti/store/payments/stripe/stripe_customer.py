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

from nti.dataserver.users import interfaces as user_interfaces

from . import stripe_io
from ... import get_user
from . import interfaces as stripe_interfaces

class StripeCustomer(stripe_io.StripeIO):

	@classmethod
	def create_customer(cls, user, coupon=None, api_key=None):
		user = get_user(user)

		profile = user_interfaces.IUserProfile(user)
		email = getattr(profile, 'email', None)
		description = getattr(profile, 'description', None)

		customer = cls.create_stripe_customer(email=email, description=description,
											  coupon=coupon, api_key=api_key)
		notify(stripe_interfaces.StripeCustomerCreated(user, customer.id))

		return customer

	@classmethod
	def delete_customer(cls, user, api_key=None):
		result = False
		user = get_user(user)
		adapted = stripe_interfaces.IStripeCustomer(user)
		if adapted.customer_id:
			result = cls.delete_stripe_customer(customer_id=adapted.customer_id,
												api_key=api_key)
			notify(stripe_interfaces.StripeCustomerDeleted(user, adapted.customer_id))
		return result

	@classmethod
	def update_customer(cls, user, customer=None, coupon=None, api_key=None):
		user = get_user(user)
		profile = user_interfaces.IUserProfile(user)
		email = getattr(profile, 'email', None)
		description = getattr(profile, 'description', None)
		adapted = stripe_interfaces.IStripeCustomer(user)
		if adapted.customer_id:
			result = cls.update_stripe_customer(customer=customer or adapted.customer_id,
												email=email,
												coupon=coupon,
												description=description,
												api_key=api_key)
			return result

		return False

	@classmethod
	def get_or_create_customer(cls, user, api_key=None):
		user = get_user(user)
		adapted = stripe_interfaces.IStripeCustomer(user)
		if adapted.customer_id is None:
			customer = cls.create_customer(user, api_key=api_key)
			result = customer.id
		else:
			result = adapted.customer_id
			# get or create the customer so it can be updated later
			customer = 	cls.get_stripe_customer(result, api_key=api_key) or \
						cls.create_customer(user, api_key=api_key)
			# reset the id in case the customer was recreated
			result = adapted.customer_id = customer.id
		return result

_StripeCustomer = StripeCustomer  # BWC
