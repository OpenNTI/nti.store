#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Payment interfaces

.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

from zope import interface

from nti.schema.field import Object
from nti.schema.field import ValidTextLine

from ..interfaces import IPriceable
from ..interfaces import IPurchaseAttempt

class ICouponPriceable(IPriceable):
	Coupon = ValidTextLine(title="The coupon", required=False)

class IRegisterPurchaseData(interface.Interface):
	object = Object(IPurchaseAttempt, title="The purchase", required=True)

class RegisterPurchaseData(object):

	def __init__(self, obj):
		self.object = obj

	@property
	def purchase(self):
		return self.object
