#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Stripe io interface.

.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import six
import sys

import stripe

from . import StripeException

_marker = object()

def _do_stripe_operation(func, *args, **kwargs):
	try:
		result = func(*args, **kwargs)
		return result
	except stripe.StripeError as e:
		raise e
	except Exception as e:
		raise StripeException(*e.args)
	
# customer

def create_stripe_customer(email, description=None, coupon=None, api_key=None):
	customer = _do_stripe_operation(stripe.Customer.create, api_key=api_key,
									email=email, coupon=coupon,
									description=description)
	return customer
		
def get_stripe_customer(customer_id, api_key=None):
	try:
		customer = _do_stripe_operation(stripe.Customer.retrieve,
										customer_id,
										api_key)
		return customer
	except stripe.InvalidRequestError, e:
		logger.error("Cannot retrieve customer %s. %s", customer_id, e)
		return None

def delete_stripe_customer(customer_id=None, customer=None, api_key=None):
	customer = customer or get_stripe_customer(customer_id, api_key)
	if customer:
		_do_stripe_operation(customer.delete)
		return True
	return False

def update_stripe_customer(customer, email=_marker, description=_marker, 
						   coupon=_marker, api_key=None):
	
	if isinstance(customer, six.string_types):
		customer = get_stripe_customer(customer_id=customer, api_key=api_key)
	
	if customer:
		if email is not _marker:
			customer.email = email
		if coupon is not _marker:
			customer.coupon = coupon
		if description is not _marker:
			customer.description = description
		# update info
		_do_stripe_operation(customer.save)
		return True
	return False

# token

def create_token(customer_id=None, number=None, exp_month=None, exp_year=None,
				 cvc=None, api_key=None, **kwargs):
	if not customer_id:
		cvc = str(cvc) if cvc else None
		cc = {
			'number': number, 'exp_month':exp_month,
			'exp_year': exp_year, 'cvc': cvc,
			'address_line1': kwargs.get('address_line1', kwargs.get('address')),
			'address_line2': kwargs.get('address_line2', kwargs.get('address2')),
			'address_city': kwargs.get('address_city', kwargs.get('city')),
			'address_state': kwargs.get('address_state', kwargs.get('state')),
			'address_zip': kwargs.get('address_zip', kwargs.get('zip')),
			'address_country': kwargs.get('address_country', kwargs.get('country'))
		}
		data = {'card':cc}
	else:
		data = {'customer': customer_id}

	token = _do_stripe_operation(stripe.Token.create, api_key=api_key, **data)
	return token
create_stripe_token = create_token	# alias
		
def get_stripe_token(token, api_key=None):
	token = _do_stripe_operation(stripe.Token.retrieve, token, api_key=api_key)
	return token
get_token = get_stripe_token # alias

# charges

def create_stripe_charge(amount, currency='USD', customer_id=None, card=None,
						 description=None, application_fee=None, metadata=None,
						 api_key=None):
	assert customer_id or card
	data = {'amount':amount, 'currency':currency}
	data['metadata'] = metadata or {}
	if description:
		data['description'] = description
	if card:
		data['card'] = card
	else:
		data['customer'] = customer_id
	if application_fee:
		data['application_fee'] = application_fee
	charge = _do_stripe_operation(stripe.Charge.create, api_key=api_key, **data)
	return charge
create_charge = create_stripe_charge

def query_stripe_charges(count=10, offset=0, customer=None, api_key=None):
	result = _do_stripe_operation(stripe.Charge.all, count=count, offset=offset, 
								  customer=customer, api_key=api_key)
	return result
	
def get_stripe_charges(customer=None, start_time=None, end_time=None, count=50, 
					   api_key=None):
	offset = 0
	start_time = int(start_time) if start_time else 0
	end_time = int(end_time) if end_time else sys.maxint

	_loop = True
	while _loop:
		charges = query_stripe_charges(	count=count, offset=offset,
										customer=customer, api_key=api_key)
		if not charges.data:
			_loop = False
		else:
			charges = charges.data
			for c in charges:
				if c.created >= start_time and c.created <= end_time:
					yield c

			offset += len(charges)
			# since the list of events is ordered desc
			# stop if an old event is not withing the range
			if start_time > charges[-1].created:
				_loop = False
get_charges = get_stripe_charges

def get_stripe_charge(charge_id, api_key=None):
	result = _do_stripe_operation(stripe.Charge.retrieve, charge_id, api_key=api_key)
	return result
get_charge = get_stripe_charge
	
def update_stripe_charge(charge, description=None, metadata=None, api_key=None):
	if isinstance(charge, six.string_types):
		charge = get_stripe_charge(charge, api_key=api_key)
	charge.description = description
	charge.metadata = {} if metadata is None else metadata
	charge.save()
update_charge = update_stripe_charge

# coupon

def get_stripe_coupon(coupon_code, api_key=None):
	coupon = _do_stripe_operation(stripe.Coupon.retrieve, coupon_code, api_key=api_key)
	return coupon

# processor class
	
class StripeIO(object):

	@classmethod
	def create_stripe_customer(cls, email, description=None, coupon=None, api_key=None):
		resut = create_stripe_customer(api_key=api_key, email=email, coupon=coupon,
									   description=description)
		return resut

	@classmethod
	def get_stripe_customer(cls, customer_id, api_key=None):
		result = get_stripe_customer(customer_id=customer_id, api_key=api_key)
		return result

	@classmethod
	def delete_stripe_customer(cls, customer_id=None, customer=None, api_key=None):
		result = delete_stripe_customer(customer_id=customer_id, customer=customer,
										api_key=api_key)
		return result

	@classmethod
	def update_stripe_customer(cls, customer, email=_marker, description=_marker,
							   coupon=_marker, api_key=None):
		result = update_stripe_customer(customer=customer, email=email, 
										description=description,
							  			coupon=coupon, api_key=api_key)
		return result

	@classmethod
	def create_token(cls, customer_id=None, number=None, exp_month=None, exp_year=None,
					 cvc=None, api_key=None, **kwargs):
		result = create_token(customer_id=customer_id, number=number,
							  exp_month=exp_month, exp_year=exp_year,
							  cvc=cvc, api_key=api_key, **kwargs)
		return result
	create_stripe_token = create_token # alias

	@classmethod
	def get_stripe_token(cls, token, api_key=None):
		result = get_stripe_token(token, api_key=api_key)
		return result
	get_token = get_stripe_token # alias

	@classmethod
	def create_stripe_charge(cls, amount, currency='USD', customer_id=None, card=None,
							 description=None, application_fee=None,
							 metadata=None, api_key=None):
		result = create_stripe_charge(amount=amount, currency=currency, 
									  customer_id=customer_id, card=card,
									  description=description,
									  metadata=metadata,
									  application_fee=application_fee,
									  api_key=api_key)
		return result
	create_charge = create_stripe_charge # alias

	@classmethod
	def get_stripe_charge(cls, charge_id, api_key=None):
		result = get_stripe_charge(charge_id=charge_id, api_key=api_key)
		return result
	get_charge = get_stripe_charge # alias
	
	@classmethod
	def get_stripe_charges(self, customer=None, start_time=None, end_time=None,
						   count=50, api_key=None):		
		result = get_stripe_charges(count=count, customer=customer, 
									start_time=start_time,
									end_time=end_time, api_key=api_key)
		return result
	get_charges = get_stripe_charges # alias

	@classmethod
	def update_stripe_charge(self, charge, description=None, metadata=None, api_key=None):		
		result = update_stripe_charge(charge=charge, description=description,
									  metadata=metadata, api_key=api_key)
		return result
	update_charge = update_stripe_charge # alias

	@classmethod
	def get_stripe_coupon(cls, coupon_code, api_key=None):
		result = get_stripe_coupon(coupon_code=coupon_code, api_key=api_key)
		return result
	get_coupon = get_stripe_coupon
