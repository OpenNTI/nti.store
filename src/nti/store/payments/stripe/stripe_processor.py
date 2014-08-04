#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from .interfaces import IStripePaymentProcessor

from .processor import SyncProcessor
from .processor import EventProcessor
from .processor import RefundProcessor
from .processor import PurchaseProcessor

@interface.implementer(IStripePaymentProcessor)
class StripePaymentProcessor(PurchaseProcessor, SyncProcessor, EventProcessor,
							 RefundProcessor):
	pass
