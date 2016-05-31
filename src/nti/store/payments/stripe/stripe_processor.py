#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from nti.store.payments.stripe.interfaces import IStripePaymentProcessor

from nti.store.payments.stripe.processor import SyncProcessor
from nti.store.payments.stripe.processor import EventProcessor
from nti.store.payments.stripe.processor import RefundProcessor
from nti.store.payments.stripe.processor import PurchaseProcessor

@interface.implementer(IStripePaymentProcessor)
class StripePaymentProcessor(PurchaseProcessor, 
							 SyncProcessor,
							 EventProcessor,
							 RefundProcessor):
	pass
