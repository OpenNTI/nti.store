#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Defines purchase error object.

.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from nti.common.representation import WithRepr

from nti.schema.schema import EqHash
from nti.schema.field import SchemaConfigured
from nti.schema.fieldproperty import createDirectFieldProperties

from .utils import MetaStoreObject

from .interfaces import IPurchaseError

@WithRepr
@EqHash('Type', 'Code', 'Message')
@interface.implementer(IPurchaseError)
class PurchaseError(SchemaConfigured):
	__metaclass__ = MetaStoreObject
	createDirectFieldProperties(IPurchaseError)

	def __str__(self):
		return self.Message

def create_purchase_error(message, type_=None, code=None):
	result = PurchaseError(Message=message, Type=type_, Code=code)
	return result
