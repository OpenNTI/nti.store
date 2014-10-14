#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Stripe utilities.

.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import six
import time
import simplejson as json

from nti.externalization.externalization import to_external_object

from ...payment_charge import UserAddress
from ...payment_charge import PaymentCharge

from ...interfaces import IPurchaseError

from .stripe_error import StripePurchaseError

from .interfaces import IStripeError
from .interfaces import IStripePurchaseError
from .interfaces import IStripeOperationError

def makenone(s, default=None):
	if isinstance(s, six.string_types):
		s = default if s == 'None' else unicode(s)
	return s

def encode_charge_description(purchase_id, username=None, 
							  customer_id=None, context=None):
	"""
	proceduce a json object for a stripe charge description
	"""
	context = to_external_object(context) if context else None 
	data = {'PurchaseID': purchase_id, 'Username':username, 
			'CustomerID': customer_id, 'Context': context}
	result = json.dumps(data)
	return result

def decode_charge_description(s):
	"""
	decode a stripe charge description
	"""
	try:
		result = json.loads(s)
	except (TypeError, ValueError):
		result = {}
	return result

def create_user_address(charge):
	"""
	creates a payment_charge.UserAddress from a stripe charge
	"""
	card = getattr(charge, 'card', None)
	if card is not None:
		address = UserAddress.create(makenone(card.address_line1),
 									 makenone(card.address_line2),
 									 makenone(card.address_city),
 									 makenone(card.address_state),
 									 makenone(card.address_zip),
 									 makenone(card.address_country))
		return address
	return UserAddress()

def get_card_info(charge):
	"""
	return card info from a stripe charge
	"""
	card = getattr(charge, 'card', None)
	name = getattr(card, 'name', None)
	last4 = getattr(card, 'last4', None)
	last4 = int(last4) if last4 is not None else None
	return (last4, name)

def create_payment_charge(charge):
	"""
	creates a payment_charge.PaymentCharge from a stripe charge
	"""
	amount = charge.amount / 100.0
	currency = charge.currency.upper()
	last4, name = get_card_info(charge)
	address = create_user_address(charge)
	created = float(charge.created or time.time())
	result = PaymentCharge(Amount=amount, Currency=currency,
						   Created=created, CardLast4=last4,
						   Address=address, Name=name)
	return result

def adapt_to_purchase_error(e):
	"""
	adapts an exception to a [purchase] error
	"""
	if IStripeError.providedBy(e):
		result = IStripeOperationError(e, None)
	else:
		result = IStripePurchaseError(e, None) or IPurchaseError(e, None)
	if result is None and isinstance(e, Exception):
		result = StripePurchaseError(e.args)
	return result
