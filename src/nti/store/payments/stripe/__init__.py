#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import logging
from zope import interface

from ... import ROUND_DECIMAL
from ... import MessageFactory

from .interfaces import IStripeException
from .interfaces import INoSuchStripeCoupon
from .interfaces import IInvalidStripeCoupon

from .stripe_error import StripePurchaseError # re-export
from .stripe_error import StripeOperationError # re-export

STRIPE = u"stripe"

@interface.implementer(IStripeException)
class StripeException(Exception):
	pass

@interface.implementer(IInvalidStripeCoupon)
class InvalidStripeCoupon(StripeException):
	pass

@interface.implementer(INoSuchStripeCoupon)
class NoSuchStripeCoupon(StripeException):
	pass

## CS: Reduce verbosity of stripe logger
from stripe.util import logger as stripe_logger
stripe_logger.setLevel(logging.ERROR)