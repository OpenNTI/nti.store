#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import six

from zope import component
from zope import interface

from nti.externalization.datastructures import InterfaceObjectIO

from nti.externalization.interfaces import IInternalObjectIO
from nti.externalization.interfaces import LocatedExternalDict
from nti.externalization.interfaces import IInternalObjectExternalizer

from .interfaces import IStripeCoupon
from .interfaces import IStripePurchaseError

def _makenone(s):
	if isinstance(s, six.string_types) and s.lower() == 'none':
		s = None
	return s

@component.adapter(IStripeCoupon)
@interface.implementer(IInternalObjectExternalizer)
class StripeCouponExternalizer(object):

	__slots__ = ('coupon',)

	def __init__(self, coupon):
		self.coupon = coupon

	def toExternalObject(self, **kwargs):
		result = LocatedExternalDict()
		result['ID'] = self.coupon.id
		if _makenone(self.coupon.duration):
			result['Duration'] = self.coupon.duration
		if self.coupon.amount_off:
			result['AmountOff'] = self.coupon.amount_off
			result['Currency'] = _makenone(self.coupon.currency) or 'USD'
		if self.coupon.percent_off:
			result['PercentOff'] = self.coupon.percent_off
		if self.coupon.duration_in_months:
			result['DurationInMonths'] = self.coupon.duration_in_months
		if self.coupon.redeem_by:
			result['RedeemBy'] = self.coupon.redeem_by
		if self.coupon.times_redeemed is not None:
			result['TimesRedeemed'] = self.coupon.times_redeemed
		if self.coupon.max_redemptions:
			result['MaxRedemptions'] = self.coupon.max_redemptions
		return result

@interface.implementer(IInternalObjectIO)
@component.adapter(IStripePurchaseError)
class StripePurchaseErrorExternal(InterfaceObjectIO):
	_ext_iface_upper_bound = IStripePurchaseError
