#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from dolmen.builtins import IString, IUnicode

from ... import MessageFactory

from .interfaces import IStripeException
from .stripe_error import StripePurchaseError # re-export

STRIPE = u"stripe"

@interface.implementer(IStripeException)
class StripeException(Exception):
	pass

class InvalidStripeCoupon(StripeException):
	pass

class NoSuchStripeCoupon(StripeException):
	pass

