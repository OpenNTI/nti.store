#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope.location import locate

from zc.intid import IIntIds

from zope.catalog.interfaces import ICatalog
from zope.catalog.interfaces import ICatalogIndex

from nti.dataserver.interfaces import ICreatedUsername

from nti.zope_catalog.catalog import Catalog
from nti.zope_catalog.index import NormalizationWrapper
from nti.zope_catalog.index import SetIndex as RawSetIndex
from nti.zope_catalog.index import ValueIndex as RawValueIndex
from nti.zope_catalog.index import AttributeValueIndex as ValueIndex
from nti.zope_catalog.index import IntegerValueIndex as RawIntegerValueIndex

from nti.zope_catalog.index import AttributeKeywordIndex
from nti.zope_catalog.string import StringTokenNormalizer
from nti.zope_catalog.datetime import TimestampToNormalized64BitIntNormalizer

from .interfaces import IPurchaseAttempt
from .interfaces import IRedeemedPurchaseAttempt

IX_ITEMS = 'items'
IX_CREATOR = 'creator'
IX_MIMETYPE = 'mimeType'
IX_REV_ITEMS = 'revItems'
IX_REDEMPTION_CODE = 'redemptionCode'
IX_STARTTIME = IX_CREATEDTIME = 'startTime'

CATALOG_NAME = 'nti.dataserver.++etc++purchase-catalog'

class MimeTypeIndex(ValueIndex):
	default_field_name = 'mimeType'
	default_interface = IPurchaseAttempt
	
class RedemptionCodeIndex(ValueIndex):
	default_field_name = 'RedemptionCode'
	default_interface = IRedeemedPurchaseAttempt
	
class CreatorRawIndex(RawValueIndex):
	pass

def CreatorIndex(family=None):
	return NormalizationWrapper(field_name='creator_username',
								interface=ICreatedUsername,
								index=CreatorRawIndex(family=family),
								normalizer=StringTokenNormalizer())

class ItemsRawIndex(RawSetIndex):
	pass

def ItemsIndex(family=None):
	return NormalizationWrapper(field_name='Items',
								interface=IPurchaseAttempt,
								normalizer=StringTokenNormalizer(),
								index=ItemsRawIndex(family=family),
								is_collection=True )

class StartTimeRawIndex(RawIntegerValueIndex):
	pass

def StartTimeIndex(family=None):
	return NormalizationWrapper(field_name='StartTime',
								interface=IPurchaseAttempt,
								index=StartTimeRawIndex(family=family),
								normalizer=TimestampToNormalized64BitIntNormalizer())


class RevItems(object):
	
	__slots__ = (b'context',)

	def __init__( self, context, default=None):
		self.context = context

	@property
	def items(self):
		if IPurchaseAttempt.providedBy(self.context):
			result = self.context.Items
			return result
	
def RevItemsIndex(family=None):
	return AttributeKeywordIndex(field_name='items', 
								 interface=RevItems,
								 family=family)


class StoreCatalog(Catalog):
	pass

def install_purchase_catalog( site_manager_container, intids=None ):
	lsm = site_manager_container.getSiteManager()
	if intids is None:
		intids = lsm.getUtility(IIntIds)

	catalog = StoreCatalog(family=intids.family)
	catalog.__name__ = CATALOG_NAME
	catalog.__parent__ = site_manager_container
	intids.register( catalog )
	lsm.registerUtility( catalog, provided=ICatalog, name=CATALOG_NAME )

	for name, clazz in ( (IX_ITEMS, ItemsIndex),
						 (IX_CREATOR, CreatorIndex),
						 (IX_MIMETYPE, MimeTypeIndex),
						 (IX_REV_ITEMS, RevItemsIndex),
						 (IX_CREATEDTIME, StartTimeIndex),
						 (IX_REDEMPTION_CODE), RedemptionCodeIndex):
		index = clazz( family=intids.family )
		assert ICatalogIndex.providedBy(index)
		intids.register( index )
		locate(index, catalog, name)
		catalog[name] = index

	return catalog
