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

from nti.externalization.representation import WithRepr

from nti.schema.schema import EqHash
from nti.schema.field import SchemaConfigured
from nti.schema.fieldproperty import createDirectFieldProperties

from ...utils import MetaStoreObject
from ...purchase_error import PurchaseError

from .interfaces import IStripePurchaseError
from .interfaces import IStripeOperationError

@interface.implementer(IStripeOperationError)
@WithRepr
@EqHash('Type', 'Code', 'Message')
class StripeOperationError(SchemaConfigured):
	__metaclass__ = MetaStoreObject
	createDirectFieldProperties(IStripeOperationError)

	def __str__(self):
		return self.Message

@interface.implementer(IStripePurchaseError)
class StripePurchaseError(PurchaseError):
	Param = FP(IStripePurchaseError['Param'])
	HttpStatus = FP(IStripePurchaseError['HttpStatus'])
