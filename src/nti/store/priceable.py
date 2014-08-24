#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Defines priceable object.

.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface
from zope.mimetype.interfaces import IContentTypeAware
from zope.schema.fieldproperty import FieldPropertyStoredThroughField as FP

from nti.externalization.representation import WithRepr

from nti.schema.schema import EqHash
from nti.schema.field import SchemaConfigured

from .utils import MetaStoreObject
from .interfaces import IPriceable
from .purchasable import get_purchasable

@interface.implementer(IPriceable, IContentTypeAware)
@WithRepr
@EqHash('NTIID', 'Quantity')
class Priceable(SchemaConfigured):

	__metaclass__ = MetaStoreObject

	NTIID = FP(IPriceable['NTIID'])
	Quantity = FP(IPriceable['Quantity'])

	def copy(self):
		result = self.__class__(NTIID=self.NTIID, Quantity=self.Quantity)
		return result

	@property
	def purchasable(self):
		result = get_purchasable(self.NTIID)
		return result

	@property
	def Currency(self):
		result = getattr(self.purchasable, 'Currency', None)
		return result

	@property
	def Provider(self):
		result = getattr(self.purchasable, 'Provider', None)
		return result

	@property
	def Amount(self):
		result = getattr(self.purchasable, 'Amount', None)
		return result

	@property
	def Fee(self):
		result = getattr(self.purchasable, 'Fee', None)
		return result

	def __str__(self):
		return self.NTIID

def create_priceable(ntiid, quantity=1):
	quantity = 1 if quantity is None else int(quantity)
	result = Priceable(NTIID=unicode(ntiid), Quantity=quantity)
	return result
