#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Stripe purchase coupon functionality.

.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import six
import sys
import time
from datetime import datetime

from dateutil import relativedelta

from nti.store.payments import _BasePaymentProcessor

from nti.store.payments.stripe import ROUND_DECIMAL
from nti.store.payments.stripe import InvalidStripeCoupon

from nti.store.payments.stripe.processor.base import BaseProcessor

from nti.store.payments.stripe.stripe_io import get_stripe_coupon

def get_coupon(coupon, api_key=None):
	if isinstance(coupon, six.string_types):
		result = get_stripe_coupon(coupon, api_key=api_key)
	else:
		result = coupon
	return result

def months_between(a, b):
	a = datetime.utcfromtimestamp(a)
	b = datetime.utcfromtimestamp(b)
	r = relativedelta.relativedelta(b, a)
	result = r.months or 0
	return abs(result)

def validate_coupon(coupon, api_key=None):
	if isinstance(coupon, six.string_types):
		coupon = get_stripe_coupon(coupon, api_key=api_key)
	result = (coupon is not None)
	if result:
		if coupon.duration == u'repeating':
			redeem_by = coupon.redeem_by
			times_redeemed = coupon.times_redeemed or 0
			duration_in_months = coupon.duration_in_months
			diff_months = months_between(coupon.created, time.time())
			max_redemptions = \
				sys.maxint if coupon.max_redemptions is None else coupon.max_redemptions
			result = \
				(times_redeemed < max_redemptions) and \
				(redeem_by is None or time.time() <= redeem_by) and \
				(duration_in_months is None or diff_months <= duration_in_months)
		elif coupon.duration == u'once':
			result = (coupon.redeem_by is None or time.time() <= coupon.redeem_by) and \
					 (not coupon.times_redeemed)
	return result

def get_and_validate_coupon(coupon=None, api_key=None):
	coupon = get_coupon(coupon=coupon, api_key=api_key) if coupon else None
	if coupon is not None and not validate_coupon(coupon=coupon, api_key=api_key):
		raise InvalidStripeCoupon()
	return coupon

def apply_coupon(amount, coupon, api_key=None):
	if isinstance(coupon, six.string_types):
		coupon = get_stripe_coupon(coupon, api_key=api_key)
	if coupon:
		if coupon.percent_off is not None:
			pcnt = coupon.percent_off / 100.0 \
				   if coupon.percent_off > 1 else coupon.percent_off
			amount = amount * (1 - pcnt)
		elif coupon.amount_off is not None:
			amount_off = coupon.amount_off / 100.0
			amount -= amount_off
	result = round(float(max(0, amount)), ROUND_DECIMAL)
	return result

class CouponProcessor(_BasePaymentProcessor, BaseProcessor):

	@classmethod
	def get_coupon(cls, coupon, api_key=None):
		result = get_coupon(coupon=coupon, api_key=api_key)
		return result

	@classmethod
	def validate_coupon(cls, coupon, api_key=None):
		result = validate_coupon(coupon=coupon, api_key=api_key)
		return result

	@classmethod
	def get_and_validate_coupon(cls, coupon=None, api_key=None):
		result = get_and_validate_coupon(coupon=coupon, api_key=api_key)
		return result

	@classmethod
	def apply_coupon(cls, amount, coupon, api_key=None):
		result = apply_coupon(amount=amount, coupon=coupon, api_key=api_key)
		return result
