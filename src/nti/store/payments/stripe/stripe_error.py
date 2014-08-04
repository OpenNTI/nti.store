#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface
from zope.schema.fieldproperty import FieldPropertyStoredThroughField as FP

from ...purchase_error import PurchaseError

from .interfaces import IStripePurchaseError

@interface.implementer(IStripePurchaseError)
class StripePurchaseError(PurchaseError):
	Param = FP(IStripePurchaseError['Param'])
	HttpStatus = FP(IStripePurchaseError['HttpStatus'])
