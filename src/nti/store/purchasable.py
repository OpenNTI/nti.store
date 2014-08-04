#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Defines purchasable object and operations on them

.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import six

from zope import component
from zope import interface
from zope.container.contained import Contained
from zope.cachedescriptors.property import Lazy
from zope.mimetype.interfaces import IContentTypeAware

from nti.dataserver import authorization
from nti.dataserver.authorization_acl import ace_allowing

from nti.dataserver.interfaces import IACLProvider
from nti.dataserver.interfaces import EVERYONE_USER_NAME

from nti.dataserver.datastructures import PersistentCreatedModDateTrackingObject

from nti.externalization.externalization import WithRepr
from nti.externalization.interfaces import LocatedExternalDict
from nti.externalization.interfaces import LocatedExternalList

from nti.mimetype.mimetype import MIME_BASE

from nti.ntiids import interfaces as nid_interfaces

from nti.schema.schema import EqHash
from nti.schema.fieldproperty import AdaptingFieldProperty
from nti.schema.fieldproperty import createDirectFieldProperties

from . import get_user

from .interfaces import IPurchasable
from .interfaces import IPurchaseHistory

from .content_bundle import ContentBundle

from .utils import to_frozenset
from .utils import to_collection
from .utils import MetaStoreObject

@interface.implementer(IPurchasable, IACLProvider, IContentTypeAware)
@WithRepr
@EqHash('NTIID',)
class Purchasable(ContentBundle):

	__metaclass__ = MetaStoreObject
	mime_type = mimeType = MIME_BASE + b'purchasable'
	
	createDirectFieldProperties(IPurchasable)
	Description = AdaptingFieldProperty(IPurchasable['Description'])

	@Lazy
	def __acl__(self):
		return (ace_allowing(EVERYONE_USER_NAME, authorization.ACT_READ, self),)

class PesistentPurchasable(Contained, 
						   Purchasable,
						   PersistentCreatedModDateTrackingObject):
	pass
	
def create_purchasable(ntiid, provider, amount, currency='USD', items=(), fee=None,
					   title=None, license_=None, author=None, description=None,
					   icon=None, thumbnail=None, discountable=False,
					   bulk_purchase=True, public=True):
	fee = float(fee) if fee is not None else None
	amount = float(amount) if amount is not None else amount
	items = to_frozenset(items) if items else frozenset((ntiid,))
	result = Purchasable(NTIID=ntiid, Provider=provider, Title=title, Author=author,
						 Items=items, Description=description, Amount=amount,
						 Currency=currency, Fee=fee, License=license_,
						 Discountable=discountable, BulkPurchase=bulk_purchase,
						 Icon=icon, Thumbnail=thumbnail, Public=True)
	return result

def get_purchasable(pid, registry=component):
	result = registry.queryUtility(IPurchasable, pid)
	return result

def get_all_purchasables(registry=component):
	result = LocatedExternalList()
	for _, purchasable in registry.getUtilitiesFor(IPurchasable):
		result.append(purchasable)
	return result

def get_purchasable_ids(registry=component):
	result = LocatedExternalList()
	for pid, _ in registry.getUtilitiesFor(IPurchasable):
		result.append(pid)
	return result

def get_available_items(user, registry=component):
	"""
	Return all item that can be purchased
	"""
	all_ids = set(get_purchasable_ids(registry=registry))
	if not all_ids:
		return {}

	# get purchase history
	purchased = set()
	user = get_user(user)
	
	history = IPurchaseHistory(user)
	for p in history:
		if p.has_succeeded() or p.is_pending():
			purchased.update(p.Items)

	available = all_ids - purchased
	result = LocatedExternalDict(
				{key:get_purchasable(key, registry=registry) for key in available})
	return result

def get_content_items(purchased_items, registry=component):
	"""
	return the nttids of the library items that were purchased
	"""
	if isinstance(purchased_items, six.string_types):
		purchased_items = to_collection(purchased_items)

	result = set()
	for item in purchased_items:
		p = get_purchasable(item, registry=registry)
		if p is not None:
			result.update(p.Items)
	return result

def get_providers(purchasables):
	result = {p.Provider for p in purchasables or ()}
	return sorted(result)

@interface.implementer(nid_interfaces.INTIIDResolver)
class _PurchasableResolver(object):

	def resolve(self, ntiid_string):
		return get_purchasable(ntiid_string)
