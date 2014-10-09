#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from nti.externalization.representation import WithRepr

from nti.schema.schema import EqHash
from nti.schema.field import SchemaConfigured
from nti.schema.fieldproperty import createDirectFieldProperties

from .utils import MetaStoreObject
from .interfaces import IRefundError

@interface.implementer(IRefundError)
@WithRepr
@EqHash('Type', 'Code', 'Message')
class RefundError(SchemaConfigured):
	__metaclass__ = MetaStoreObject
	createDirectFieldProperties(IRefundError)

	def __str__(self):
		return self.Message

def create_refudn_error(message, type_=None, code=None):
	result = RefundError(Message=message, Type=type_, Code=code)
	return result
