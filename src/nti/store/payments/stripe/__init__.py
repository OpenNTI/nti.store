#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import logging

from zope import interface

from nti.store import ROUND_DECIMAL
from nti.store import MessageFactory

from nti.store.payments.stripe.interfaces import IStripeException
from nti.store.payments.stripe.interfaces import INoSuchStripeCoupon
from nti.store.payments.stripe.interfaces import IInvalidStripeCoupon

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


# Reduce verbosity of stripe logger
from stripe.util import logger as stripe_logger
stripe_logger.setLevel(logging.ERROR)
