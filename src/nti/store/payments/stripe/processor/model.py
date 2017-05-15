#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from nti.store.payments.stripe.interfaces import IStripePaymentProcessor

from nti.store.payments.stripe.processor.event import EventProcessor

from nti.store.payments.stripe.processor.purchase import PurchaseProcessor

from nti.store.payments.stripe.processor.refund import RefundProcessor

from nti.store.payments.stripe.processor.sync import SyncProcessor


@interface.implementer(IStripePaymentProcessor)
class StripePaymentProcessor(PurchaseProcessor,
                             SyncProcessor,
                             EventProcessor,
                             RefundProcessor):
    pass
