#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Defines purchase history.

.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component
from zope import interface
from zope import lifecycleevent

from zope.annotation import factory as an_factory

from zope.container.contained import Contained

from zope.deprecation import deprecated

from zope.intid.interfaces import IIntIds

from zope.location import locate

from zope.location.interfaces import ISublocations

from ZODB.interfaces import IConnection

import BTrees

from persistent import Persistent

from nti.dataserver.interfaces import IUser

from nti.externalization.oids import to_external_ntiid_oid
from nti.externalization.interfaces import LocatedExternalDict
from nti.externalization.interfaces import LocatedExternalList

from nti.ntiids.ntiids import find_object_with_ntiid

from nti.store import get_user
from nti.store import get_purchase_catalog

from nti.store.interfaces import IPurchaseAttempt
from nti.store.interfaces import IPurchaseHistory

from nti.store.purchasable import get_purchasable
from nti.store.purchasable import get_purchasables

from nti.store.purchase_index import IX_ITEMS
from nti.store.purchase_index import IX_CREATOR
from nti.store.purchase_index import IX_MIMETYPE
from nti.store.purchase_index import IX_CREATEDTIME

from nti.store.utils import NONGIFT_PURCHASE_ATTEMPT_MIME_TYPES as NONGIFT_MIME_TYPES

from nti.store.utils import to_frozenset

from nti.zope_catalog.catalog import ResultSet

# classes

deprecated('_PurchaseIndex', 'Use new purchase storage')
class _PurchaseIndex(Persistent):
	pass

@component.adapter(IUser)
@interface.implementer(IPurchaseHistory, ISublocations)
class PurchaseHistory(Contained, Persistent):

	family = BTrees.family64

	def __init__(self):
		self.reset()

	def reset(self):
		self._purchases = self.family.OO.OOBTree()
		self._items_activated = self.family.OO.OOTreeSet()

	@property
	def user(self):
		return self.__parent__

	@property
	def _intids(self):
		return component.getUtility(IIntIds)

	def activate_items(self, items):
		"""
		register/activates the purchasables (NTIIDs)
		"""
		items = to_frozenset(items)
		self._items_activated.update(items)

	def deactivate_items(self, items):
		"""
		unregister the purchasables (NTIIDs)
		"""
		count = 0
		items = to_frozenset(items)
		for item in items:
			if item in self._items_activated:
				count += 1
				self._items_activated.remove(item)
		return count

	def is_item_activated(self, item):
		return item in self._items_activated

	def add_purchase(self, purchase):
		# locate before firing events
		locate(purchase, self)
		# add to connection and fire event
		IConnection(self).add(purchase)
		lifecycleevent.created(purchase)
		lifecycleevent.added(purchase)  # get an iid
		# now we can get an OID/NTIID
		result = purchase.id = unicode(to_external_ntiid_oid(purchase))
		self._purchases[purchase.id] = purchase
		return result
	add = append = register_purchase = add_purchase

	def remove_purchase(self, purchase):
		try:
			pid = getattr(purchase, 'id', purchase)
			del self._purchases[pid]
			lifecycleevent.removed(purchase)  # remove iid
			result = True
		except KeyError:
			result = False
		return result
	remove = remove_purchase

	def get_purchase(self, pid):
		try:
			pid = getattr(pid, 'id', pid)
			result = self._purchases[pid]
		except KeyError:
			result = None
		return result
	get = get_purchasable

	def get_purchase_state(self, pid):
		p = self.get_purchase(pid)
		return p.State if p is not None else None

	def get_pending_purchases(self, items=None):
		items = to_frozenset(items) if items else None
		for p in self.values():
			if		(p.is_pending() or p.is_unknown()) \
				and (not items or to_frozenset(p.Items).intersection(items)):
				yield p

	def get_purchase_history_by_item(self, item):
		return get_purchase_history_by_item(self.user, item)

	def get_purchase_history(self, start_time=None, end_time=None):
		result = get_purchase_history(self.user, start_time, end_time)
		return iter(result)

	def has_history_by_item(self, purchasable_id):
		return has_history_by_item(self.user, purchasable_id)

	def clear(self):
		result = 0
		for p in list(self.values()):
			self.remove_purchase(p)
			result += 1
		return result

	def values(self):
		return self._purchases.values()

	def __iter__(self):
		return iter(self._purchases.values())

	def __len__(self):
		return len(self._purchases)

	def sublocations(self):
		for purchase in self.values():
			yield purchase

	def _v_check(self):
		import BTrees.check
		for item in (self._items_activated, self._purchases):
			item._check()
			BTrees.check.check(item)

_PurchaseHistoryFactory = an_factory(PurchaseHistory)

# functions

def activate_items(user, items):
	user = get_user(user)
	if user is not None:
		hist = IPurchaseHistory(user)
		hist.activate_items(items)
		return True
	return False

def deactivate_items(user, items):
	user = get_user(user)
	if user is not None:
		hist = IPurchaseHistory(user)
		result = hist.deactivate_items(items)
		return result
	return None

def is_item_activated(user, item):
	user = get_user(user)
	if user is not None:
		hist = IPurchaseHistory(user)
		result = hist.is_item_activated(item)
		return result
	return False

def get_purchase_attempt(purchase_id, user=None):
	result = find_object_with_ntiid(purchase_id)
	result = result if IPurchaseAttempt.providedBy(result) else None
	if result is not None and user:
		user = get_user(user)
		if user is not None:  # validate
			result = None if result.creator != user else result
	return result

def remove_purchase_attempt(purchase, user=None):
	user = get_user(user) or purchase.creator
	if user is not None:
		hist = IPurchaseHistory(user)
		hist.deactivate_items(purchase.Items)
		result = hist.remove_purchase(purchase)
		return result
	return False

def get_pending_purchases(user, items=None):
	user = get_user(user)
	if user is not None:
		hist = IPurchaseHistory(user)
		result = LocatedExternalList(hist.get_pending_purchases(items))
		return result
	return ()

def get_purchase_history(user, start_time=None, end_time=None, catalog=None):
	user = get_user(user)
	if user is None:
		result = ()
	else:
		intids = component.getUtility(IIntIds)
		catalog = get_purchase_catalog() if catalog is None else catalog
		query = {
			IX_CREATOR:{'any_of': (user.username,)},
			IX_MIMETYPE: {'any_of': NONGIFT_MIME_TYPES},
			IX_CREATEDTIME: {'between': (start_time, end_time)}
		}
		doc_ids = catalog.apply(query) or ()
		result = LocatedExternalList(ResultSet(doc_ids, intids, ignore_invalid=True))
	return result

def get_purchase_ids_by_items(user, *purchasables):
	catalog = get_purchase_catalog()
	query = {
		IX_ITEMS:{'any_of': purchasables},
		IX_CREATOR: {'any_of': (user.username,)},
		IX_MIMETYPE: {'any_of': NONGIFT_MIME_TYPES}
	}
	result = catalog.apply(query) or ()
	return result

def get_purchase_history_by_item(user, purchasable_id):
	user = get_user(user)
	if user is None:
		result = ()
	else:
		intids = component.getUtility(IIntIds)
		doc_ids = get_purchase_ids_by_items(user, purchasable_id)
		result = LocatedExternalList(ResultSet(doc_ids, intids, ignore_invalid=True))
	return result

def has_history_by_item(user, purchasable_id):
	user = get_user(user)
	if user is not None:
		doc_ids = get_purchase_ids_by_items(user, purchasable_id)
		return bool(doc_ids)
	return False

def register_purchase_attempt(purchase, user):
	user = get_user(user)
	if user is not None:
		hist = IPurchaseHistory(user)
		hist.add_purchase(purchase)
		return purchase.id
	return None
add_purchase_attempt = register_purchase_attempt

def get_purchasable_ids(registry=component):
	result = [p.NTIID for p in get_purchasables(registry)]
	return result

def get_available_items(user, registry=component):
	"""
	Return all item that can be purchased
	"""
	result = LocatedExternalDict()
	all_ids = set(get_purchasable_ids(registry=registry))
	if all_ids:
		# get purchase history
		purchased = set()
		user = get_user(user)
		history = IPurchaseHistory(user)
		for p in history:
			if p.has_succeeded() or p.is_pending():
				purchased.update(p.Items)

		available = all_ids - purchased
		result.update({key:get_purchasable(key, registry=registry) for key in available})
	return result
