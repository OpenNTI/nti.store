#!/usr/bin/env python
# -*- coding: utf-8 -*
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
from zope.cachedescriptors.property import Lazy
from zope.mimetype import interfaces as zmime_interfaces

from nti.dataserver import authorization
from nti.dataserver import authorization_acl as a_acl
from nti.dataserver import interfaces as nti_interfaces

from nti.externalization.persistence import NoPickle
from nti.externalization.externalization import WithRepr
from nti.externalization.interfaces import LocatedExternalDict
from nti.externalization.interfaces import LocatedExternalList

from nti.ntiids import interfaces as nid_interfaces

from nti.schema.schema import EqHash
from nti.schema.fieldproperty import AdaptingFieldProperty
from nti.schema.fieldproperty import createDirectFieldProperties

from . import utils
from . import get_user
from . import content_bundle
from . import interfaces as store_interfaces

@interface.implementer(store_interfaces.IPurchasable,
					   nti_interfaces.IACLProvider,
					   zmime_interfaces.IContentTypeAware)
@WithRepr
@NoPickle
@EqHash('NTIID',)
class Purchasable(content_bundle.ContentBundle):

	__metaclass__ = utils.MetaStoreObject

	# create all interface fields
	createDirectFieldProperties(store_interfaces.IPurchasable)

	# Override Description to adapt to a content fragment
	Description = AdaptingFieldProperty(store_interfaces.IPurchasable['Description'])

	@Lazy
	def __acl__(self):
		return (a_acl.ace_allowing(nti_interfaces.EVERYONE_USER_NAME,
								   authorization.ACT_READ, self),)

def create_purchasable(ntiid, provider, amount, currency='USD', items=(), fee=None,
					   title=None, license_=None, author=None, description=None,
					   icon=None, thumbnail=None, discountable=False,
					   bulk_purchase=True):
	fee = float(fee) if fee is not None else None
	amount = float(amount) if amount is not None else amount
	items = utils.to_frozenset(items) if items else frozenset((ntiid,))
	result = Purchasable(NTIID=ntiid, Provider=provider, Title=title, Author=author,
						 Items=items, Description=description, Amount=amount,
						 Currency=currency, Fee=fee, License=license_,
						 Discountable=discountable, BulkPurchase=bulk_purchase,
						 Icon=icon, Thumbnail=thumbnail)
	return result

def get_purchasable(pid, registry=component):
	result = registry.queryUtility(store_interfaces.IPurchasable, pid)
	return result

def get_all_purchasables(registry=component):
	result = LocatedExternalList()
	for _, purchasable in registry.getUtilitiesFor(store_interfaces.IPurchasable):
		result.append(purchasable)
	return result

def get_purchasable_ids(registry=component):
	result = LocatedExternalList()
	for pid, _ in registry.getUtilitiesFor(store_interfaces.IPurchasable):
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
	
	history = store_interfaces.IPurchaseHistory(user)
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
		purchased_items = utils.to_collection(purchased_items)

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
