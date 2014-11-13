#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Defines purchase history.

.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import BTrees
from BTrees.Length import Length

import zope.intid

from zope import component
from zope import interface
from zope import lifecycleevent
from zope.location import locate
from zope.container.contained import Contained
from zope.annotation import factory as an_factory
from zope.location.interfaces import ISublocations

from ZODB.interfaces import IConnection

from persistent import Persistent

from nti.dataserver.interfaces import IUser

from nti.externalization.oids import to_external_ntiid_oid
from nti.externalization.interfaces import LocatedExternalList

from nti.ntiids import ntiids

from nti.utils.property import Lazy

from nti.zodb.containers import time_to_64bit_int

from . import get_user

from .utils import to_frozenset

from .interfaces import IPurchaseAttempt
from .interfaces import IPurchaseHistory

def _check_valid(p, uid, purchasable_id=None, intids=None, debug=True):
	if not IPurchaseAttempt.providedBy(p):
		return False

	# they exist in the backward index so that queryObject works,
	# but they do not actually have an intid that matches
	# (_ds_intid). This means that removal cannot work for
	# those cases that allow removal (courses). We think (hope) this is a
	# rare problem, so we pretend it doesn't exist, only logging loudly.
	# This could also be a corruption in our internal indexes.
	if intids is None:
		intids = component.getUtility(zope.intid.IIntIds)
	queried = intids.queryId(p)
	if queried != uid:
		try:
			p._p_activate()
		except KeyError:
			# It looks like queryId can hide the POSKeyError
			# by generally catching KeyError
			if debug:
				logger.exception("Broken object %r", p)
			else:
				logger.error("Broken object %r", p)
		logger.warn("Found inconsistent purchase attempt for " +
					"purchasable %s, ignoring: %r (%s %s). ids (%s, %s)",
					purchasable_id, p, getattr(p, '__class__', None),
					type(p), queried, uid)
		return False
	return True

def _check_index(index):
	import BTrees.check
	index.purchases._check()
	index.item_index._check()
	index.time_index._check()
	BTrees.check.check(index.purchases)
	BTrees.check.check(index.item_index)
	BTrees.check.check(index.time_index)

class _PurchaseIndex(Persistent):

	family = BTrees.family64

	def __init__(self):
		self.__len = Length()
		self.item_index = self.family.OO.OOBTree()
		self.time_index = self.family.II.LLBTree()
		self.purchases = self.family.II.LLTreeSet()

	@Lazy
	def _intids(self):
		return component.getUtility(zope.intid.IIntIds)

	# addition

	def _addToIntIdIndex(self, iid=None):
		if iid is not None:
			self.purchases.add(iid)
			self.__len.change(1)
			return True
		return False

	def _addToTimeIndex(self, startTime, iid=None):
		if iid is not None and startTime:
			map_key = time_to_64bit_int(startTime)
			self.time_index[map_key] = iid
			return True
		return False

	def _addToItemIndex(self, items=(), iid=None):
		if iid is not None:
			for item in  items or ():
				item_set = self.item_index.get(item)
				if item_set is None:
					item_set = self.item_index[item] = self.family.II.LLTreeSet()
				item_set.add(iid)
			return True
		return False

	def add(self, purchase):
		iid = self._intids.getId(purchase)
		result = self._addToIntIdIndex(iid)
		self._addToItemIndex(purchase.Items, iid)
		self._addToTimeIndex(purchase.StartTime, iid)
		return result

	# removal

	def _removeFromIntIdIndex(self, iid):
		if iid is not None and iid in self.purchases:
			self.__len.change(-1)
			self.purchases.remove(iid)
			return True
		return False

	def _removeFromTimeIndex(self, startTime):
		if startTime is not None:
			result = self.time_index.pop(time_to_64bit_int(startTime), None)
			return result is not None
		return False

	def _removeFromItemIndex(self, items=(), iid=None):
		if iid is not None:
			for item in items or ():
				item_set = self.item_index.get(item)
				if item_set and item_set.has_key(iid):
					item_set.remove(iid)
			return True
		return False

	def remove(self, purchase):
		iid = self._intids.queryId(purchase)
		self._removeFromTimeIndex(purchase.StartTime)
		self._removeFromItemIndex(purchase.Items, iid)
		result = self._removeFromIntIdIndex(iid)
		return result

	# retrieve

	def has_history_by_item(self, purchasable_id):
		# Actually load the history to perform consistency checks
		items = list(self.get_history_by_item(purchasable_id))
		return len(items) > 0

	def get_history_by_item(self, purchasable_id):
		item_set = self.item_index.get(purchasable_id) or ()
		for uid in item_set:
			p = self._intids.queryObject(uid)
			if _check_valid(p, uid, purchasable_id, intids=self._intids):
				yield p

	def get_history_by_time(self, start_time=None, end_time=None):
		end_time = time_to_64bit_int(end_time) if end_time is not None else None
		start_time = time_to_64bit_int(start_time) if start_time is not None else None
		for _, iid in self.time_index.iteritems(start_time, end_time):
			p = self._intids.queryObject(iid)
			if _check_valid(p, iid, intids=self._intids):
				yield p

	def values(self):
		for iid in self.purchases:
			p = self._intids.queryObject(iid)
			if _check_valid(p, iid, intids=self._intids):
				yield p

	def __iter__(self):
		return self.values()

	def __len__(self):
		return self.__len.value

	def __nonzero__(self):
		return True
	__bool__ = __nonzero__

	def _v_check(self):
		_check_index(self)

@component.adapter(IUser)
@interface.implementer(IPurchaseHistory, ISublocations)
class PurchaseHistory(Contained, Persistent):

	family = BTrees.family64

	def __init__(self):
		self._index = _PurchaseIndex()
		self._items_activated = self.family.OO.OOTreeSet()

	@property
	def index(self):
		return self._index

	@property
	def user(self):
		return self.__parent__

	@Lazy
	def _intids(self):
		return component.getUtility(zope.intid.IIntIds)

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

	def register_purchase(self, purchase):
		# locate before firing events
		locate(purchase, self)
		# add to connection before firing event
		IConnection(self).add(purchase)
		# fire events
		lifecycleevent.created(purchase)
		lifecycleevent.added(purchase)  # get an iid
		self._index.add(purchase)
		# set id/__name__
		purchase.id = unicode(to_external_ntiid_oid(purchase))
		return purchase.id
	add = add_purchase = register_purchase

	def remove_purchase(self, purchase):
		if self._index.remove(purchase):
			lifecycleevent.removed(purchase) # remove iid
			return True
		return False

	@classmethod
	def get_purchase(cls, pid):
		result = ntiids.find_object_with_ntiid(pid)
		return result

	def get_purchase_state(self, pid):
		p = self.get_purchase(pid)
		return p.State if p else None

	def get_pending_purchases(self, items=None):
		items = to_frozenset(items) if items else None
		for p in self.values():
			if	(p.is_pending() or p.is_unknown()) and \
				(not items or to_frozenset(p.Items).intersection(items)):
				yield p

	def get_purchase_history_by_item(self, item):
		return self._index.get_history_by_item(item)

	def get_purchase_history(self, start_time=None, end_time=None):
		return self._index.get_history_by_time(start_time, end_time)

	def has_history_by_item(self, purchasable_id):
		return self._index.has_history_by_item(purchasable_id)

	def clear(self):
		result = 0
		for p in list(self.values()):
			self.remove_purchase(p)
			result +=1
		return result
				
	def values(self):
		return self._index.values()

	def __iter__(self):
		return self._index.values()

	def __len__(self):
		return len(self._index)

	def sublocations(self):
		for iid in self._index.purchases:
			purchase = self._intids.queryObject(iid)
			if getattr(purchase, '__parent__',None) is self:
				yield purchase

	def _v_check(self):
		import BTrees.check
		self._index._v_check()
		self._items_activated._check()
		BTrees.check.check(self._items_activated)

_PurchaseHistoryFactory = an_factory(PurchaseHistory)

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
	result = ntiids.find_object_with_ntiid(purchase_id)
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

def get_purchase_history(user, start_time=None, end_time=None):
	user = get_user(user)
	if user is not None:
		hist = IPurchaseHistory(user)
		result = LocatedExternalList(hist.get_purchase_history(start_time, end_time))
		return result
	return ()

def has_history_by_item(user, purchasable_id):
	user = get_user(user)
	if user is not None:
		hist = IPurchaseHistory(user)
		result = hist.has_history_by_item(purchasable_id)
		return result
	return False

def get_purchase_history_by_item(user, purchasable_id):
	user = get_user(user)
	if user is not None:
		hist = IPurchaseHistory(user)
		result = LocatedExternalList(hist.get_purchase_history_by_item(purchasable_id))
		return result
	return ()

def register_purchase_attempt(purchase, user):
	user = get_user(user)
	if user is not None:
		hist = IPurchaseHistory(user)
		hist.register_purchase(purchase)
		return purchase.id
	return None
