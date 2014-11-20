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

from ... import _BasePaymentProcessor

from .. import InvalidStripeCoupon
from ..stripe_io import get_stripe_coupon

from .base import BaseProcessor

def get_coupon(coupon, api_key=None):
	if isinstance(coupon, six.string_types):
		result = get_stripe_coupon(coupon, api_key=api_key)
	else:
		result = coupon
	return result
	
def validate_coupon(coupon, api_key=None):
	if isinstance(coupon, six.string_types):
		coupon = get_stripe_coupon(coupon, api_key=api_key)
	result = (coupon is not None)
	if result:
		if coupon.duration == u'repeating':
			times_redeemed = coupon.times_redeemed or 0 
			max_redemptions = \
				sys.maxint if coupon.max_redemptions is None else coupon.max_redemptions
			result = \
				(times_redeemed < max_redemptions) and \
				(coupon.redeem_by is None or time.time() <= coupon.redeem_by) and \
				(coupon.duration_in_months is None or coupon.duration_in_months > 0)
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
	result = float(max(0, amount))
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
