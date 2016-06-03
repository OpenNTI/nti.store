#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import six
import time

from zope import component

from nti.common.string import safestr

from nti.externalization.externalization import to_external_object

from nti.store.interfaces import IPurchaseError
from nti.store.interfaces import IStorePurchaseMetadataProvider

from nti.store.payment_charge import UserAddress
from nti.store.payment_charge import PaymentCharge

from nti.store.payments.stripe.interfaces import IStripeError
from nti.store.payments.stripe.interfaces import IStripePurchaseError
from nti.store.payments.stripe.interfaces import IStripeOperationError

from nti.store.payments.stripe.stripe_error import StripePurchaseError

def makenone(s, default=None):
	if isinstance(s, six.string_types):
		s = default if s == 'None' else unicode(s)
	return s

def flatten_context(context=None):
	if not context:
		return None
	result = {}
	for k, v in context.items():
		if v is not None and not isinstance(v, six.string_types):
			v = str(v)
		v = safestr(v) if v else v
		if not v:
			continue
		result[k] = v[:500]  # stripe requirement
	return result

def get_charge_metata(purchase_id, username=None,
					  customer_id=None, context=None):
	"""
	proceduce a json object for a stripe charge description
	"""
	context = to_external_object(context) if context else None
	data = {'PurchaseID': purchase_id}
	if username:
		data['Username'] = username
	if customer_id:
		data['CustomerID'] = customer_id

	for _, meta_subscriber in list(component.getUtilitiesFor(IStorePurchaseMetadataProvider)):
		data = meta_subscriber.update_metadata(data)

	context = flatten_context(context)
	if context:
		data.update(flatten_context(context))
	return data

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
		result = StripePurchaseError(Type=u"PurchaseError")
		args = getattr(e, 'args', ())
		message = unicode(' '.join(map(str, args)))
		result.Message = message
	return result

def replace_items_coupon(context, coupon=None):
	for item in getattr(context, 'Items', context) or ():
		item.Coupon = coupon
