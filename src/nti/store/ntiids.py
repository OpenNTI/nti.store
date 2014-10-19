#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Defines purchasable object and operations on them

.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component
from zope import interface

import zope.intid

from nti.externalization.integer_strings import from_external_string

from nti.ntiids.ntiids import get_parts 
from nti.ntiids.interfaces import INTIIDResolver

from nti.utils.property import Lazy

from .purchasable import get_purchasable

@interface.implementer(INTIIDResolver)
class _PurchasableResolver(object):

	singleton = None
	
	def __new__(cls, *args, **kwargs):
		if not cls.singleton:
			cls.singleton = super(_PurchasableResolver, cls).__new__(cls)
		return cls.singleton
	
	def resolve(self, ntiid_string):
		return get_purchasable(ntiid_string)

_CourseResolver = _PurchasableResolver # alias BWC

@interface.implementer(INTIIDResolver)
class _GiftPurchaseAttemptResolver(object):

	singleton = None
	
	def __new__(cls, *args, **kwargs):
		if not cls.singleton:
			cls.singleton = super(_GiftPurchaseAttemptResolver, cls).__new__(cls)
		return cls.singleton
	
	@Lazy
	def intids(self):
		return component.getUtility(zope.intid.IIntIds)
		
	def resolve(self, ntiid_string):
		parts = get_parts(ntiid_string)
		if parts.nttype == 'giftpurchaseattempt':
			try:
				uid = from_external_string(parts.specific)
				result = self.intids.queryObject(uid)
				return result
			except StandardError:
				pass
		return None
