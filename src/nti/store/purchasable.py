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
from zope.container.contained import Contained
from zope.mimetype.interfaces import IContentTypeAware

from nti.common.property import Lazy
from nti.common.property import alias

from nti.dataserver import authorization
from nti.dataserver.authorization_acl import ace_allowing

from nti.dataserver.interfaces import IACLProvider
from nti.dataserver.interfaces import EVERYONE_USER_NAME

from nti.dublincore.datastructures import PersistentCreatedModDateTrackingObject

from nti.externalization.representation import WithRepr
from nti.externalization.interfaces import LocatedExternalList
from nti.externalization.interfaces import IInternalObjectExternalizer

from nti.schema.schema import EqHash
from nti.schema.fieldproperty import AdaptingFieldProperty
from nti.schema.fieldproperty import createDirectFieldProperties

from .utils import to_frozenset
from .utils import to_collection
from .utils import MetaStoreObject

from .item_bundle import ItemBundle

from .interfaces import IPurchasable
from .interfaces import IPurchasableVendorInfo
from .interfaces import IPurchasableChoiceBundle

@interface.implementer(IPurchasableVendorInfo, IInternalObjectExternalizer)
class DefaultPurchasableVendorInfo(dict):
	"""
	The default representation of vendor info.
	"""
	
	def toExternalObject(self, *args, **kwargs):
		return dict(self)
	
@interface.implementer(IPurchasable, IACLProvider, IContentTypeAware)
@WithRepr
@EqHash('NTIID',)
class Purchasable(PersistentCreatedModDateTrackingObject, ItemBundle, Contained):

	__metaclass__ = MetaStoreObject
	
	createDirectFieldProperties(IPurchasable)
	Description = AdaptingFieldProperty(IPurchasable['Description'])

	isPublic = alias('Public')
	isGiftable = alias('Giftable')

	@Lazy
	def __acl__(self):
		return (ace_allowing(EVERYONE_USER_NAME, authorization.ACT_READ, self),)

@interface.implementer(IPurchasableChoiceBundle)
class PurchasableChoiceBundle(Purchasable):
	__external_class_name__ = 'Purchasable'

def create_purchasable(ntiid, provider, amount, currency='USD', items=(), fee=None,
					   title=None, license_=None, author=None, description=None,
					   icon=None, thumbnail=None, discountable=False, giftable=False,
					   redeemable=False, bulk_purchase=True, public=True, 
					   vendor_info=None, factory=Purchasable, **kwargs):
	
	fee = float(fee) if fee is not None else None
	amount = float(amount) if amount is not None else amount
	items = to_frozenset(items) if items else frozenset((ntiid,))
	vendor = IPurchasableVendorInfo(vendor_info, None)
	
	result = factory(NTIID=ntiid, Provider=provider, Title=title, Author=author,
					 Items=items, Description=description, Amount=amount,
					 Currency=currency, Fee=fee, License=license_, Giftable=giftable,
					 Redeemable=redeemable, Discountable=discountable, 
					 BulkPurchase=bulk_purchase, Icon=icon, Thumbnail=thumbnail, 
					 Public=public, VendorInfo=vendor)
	return result

def get_purchasable(pid, registry=component):
	result = registry.queryUtility(IPurchasable, pid)
	return result

def get_purchasables(registry=component, provided=IPurchasable):
	result = LocatedExternalList()
	for _, purchasable in registry.getUtilitiesFor(IPurchasable):
		result.append(purchasable)
	return result
get_all_purchasables = get_purchasables

def get_purchasable_choice_bundles(registry=component):
	return get_purchasables(registry=registry, provided=IPurchasableChoiceBundle)

def expand_purchase_item_ids(context, registry=component):
	"""
	return the ids of the items that were purchased
	"""
	result = set()
	context = getattr(context, 'Items', context)
	purchasables_ids = to_collection(context)
	for item in purchasables_ids:
		p = get_purchasable(item, registry=registry)
		if p is not None:
			result.update(p.Items)
	return result

def get_providers(purchasables):
	result = {p.Provider for p in purchasables or ()}
	return sorted(result)
