#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
Defines purchase error object.

.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component
from zope import interface

from nti.externalization.externalization import WithRepr

from nti.schema.schema import EqHash
from nti.schema.field import SchemaConfigured
from nti.schema.fieldproperty import createDirectFieldProperties

from . import utils
from . import interfaces as store_interfaces

@interface.implementer(store_interfaces.IPurchaseError)
@WithRepr
@EqHash('Type', 'Code', 'Message')
class PurchaseError(SchemaConfigured):
	__metaclass__ = utils.MetaStoreObject
	createDirectFieldProperties(store_interfaces.IPurchaseError)

	def __str__(self):
		return self.Message

def create_purchase_error(message, type_=None, code=None):
	result = PurchaseError(Message=message, Type=type_, Code=code)
	return result

@component.adapter(store_interfaces.INTIStoreException)
@interface.implementer(store_interfaces.IPurchaseError)
def nti_store_exception_adpater(error):
	result = PurchaseError(Type=u"NTIException")
	args = getattr(error, 'args', ())
	message = unicode(' '.join(map(str, args)))
	result.Message = message or 'Unspecified Exception'
	return result
