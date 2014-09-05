#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component
from zope import interface

from dolmen.builtins import IDict

from .interfaces import IPurchaseError
from .interfaces import INTIStoreException
from .interfaces import IPurchasableVendorInfo
from .interfaces import IPurchaseAttemptContext

from .purchase_error import PurchaseError
from .purchasable import DefaultPurchasableVendorInfo
from .purchase_attempt import DefaultPurchaseAttemptContext

@component.adapter(IDict)
@interface.implementer(IPurchasableVendorInfo)
def _mapping_to_vendorinfo(data):
	return DefaultPurchasableVendorInfo(**data)
	
@component.adapter(IDict)
@interface.implementer(IPurchaseAttemptContext)
def _mapping_to_purchase_attempt_context(data):
	return DefaultPurchaseAttemptContext(**data)

@component.adapter(INTIStoreException)
@interface.implementer(IPurchaseError)
def _nti_store_exception_adpater(error):
	result = PurchaseError(Type=u"NTIException")
	args = getattr(error, 'args', ())
	message = unicode(' '.join(map(str, args)))
	result.Message = message or 'Unspecified Exception'
	return result
