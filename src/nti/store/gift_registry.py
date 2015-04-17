#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
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

from ZODB.interfaces import IConnection

from persistent import Persistent

from nti.common.property import Lazy
from nti.common.time import time_to_64bit_int

from nti.dataserver.interfaces import ACE_DENY_ALL
from nti.dataserver.interfaces import ALL_PERMISSIONS
from nti.dataserver.containers import CaseInsensitiveCheckingLastModifiedBTreeContainer

from nti.dataserver.authorization import ROLE_ADMIN
from nti.dataserver.authorization_acl import ace_allowing
from nti.dataserver.authorization_acl import acl_from_aces

from nti.externalization.oids import to_external_ntiid_oid
from nti.externalization.interfaces import LocatedExternalList

from nti.ntiids.ntiids import find_object_with_ntiid

from nti.zope_catalog.catalog import ResultSet

from .utils import to_frozenset
from .utils import GIFT_PURCHASE_ATTEMPT_MIME_TYPES

from .purchase_index import IX_CREATOR
from .purchase_index import IX_MIMETYPE
from .purchase_index import IX_CREATEDTIME

from .interfaces import IGiftRegistry
from .interfaces import IUserGiftHistory
from .interfaces import IGiftPurchaseAttempt

from . import get_catalog

@interface.implementer(IUserGiftHistory)
class UserGiftHistory(Contained, Persistent):

	family = BTrees.family64

	def __init__(self):
		self.__len = Length()
		self.time_index = self.family.II.LLBTree()
		self.purchases = self.family.II.LLTreeSet()

	@property
	def creator(self):
		return self.__parent__.__name__
	
	@Lazy
	def _intids(self):
		return component.getUtility(zope.intid.IIntIds)

	# addition
	
	def _addToPurchaseIndex(self, iid=None):
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
	
	def add(self, purchase):
		iid = self._intids.getId(purchase)
		result = self._addToPurchaseIndex(iid)
		self._addToTimeIndex(purchase.StartTime, iid)
		return result
	register_purchase = add

	# removal
	
	def _removeFromPurchaseIndex(self, iid):
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
		
	def remove(self, purchase):
		iid = self._intids.queryId(purchase)
		self._removeFromTimeIndex(purchase.StartTime)
		result = self._removeFromPurchaseIndex(iid)
		return result

	# retrieval
	
	def get_history_by_time(self, start_time=None, end_time=None):
		end_time = time_to_64bit_int(end_time) if end_time is not None else None
		start_time = time_to_64bit_int(start_time) if start_time is not None else None
		for _, iid in self.time_index.iteritems(start_time, end_time):
			p = self._intids.queryObject(iid)
			if IGiftPurchaseAttempt.providedBy(p):
				yield p

	def get_pending_purchases(self, items=None):
		items = to_frozenset(items) if items else None
		for p in self.values():
			if 	(p.is_pending() or p.is_unknown()) and \
				(not items or to_frozenset(p.Items).intersection(items)):
				yield p
	
	def values(self):
		for iid in self.purchases:
			p = self._intids.queryObject(iid)
			if IGiftPurchaseAttempt.providedBy(p):
				yield p

	def __iter__(self):
		return self.values()

	def __len__(self):
		return self.__len.value

	def __nonzero__(self):
		return True
	__bool__ = __nonzero__
	
	@property
	def __acl__(self):
		aces = [ace_allowing(ROLE_ADMIN, ALL_PERMISSIONS, UserGiftHistory)]
		creator = self.creator
		if creator is not None:
			aces.append(ace_allowing(creator, ALL_PERMISSIONS, UserGiftHistory))
		aces.append(ACE_DENY_ALL)
		return acl_from_aces(aces)

@interface.implementer(IGiftRegistry)
class GiftRegistry(CaseInsensitiveCheckingLastModifiedBTreeContainer):
	
	def __init__(self):
		super(GiftRegistry,self).__init__()

	@property
	def Items(self):
		return dict(self)
	
	@property
	def intids(self):
		result = component.getUtility(zope.intid.IIntIds)
		return result
		
	def register_purchase(self, username, purchase):
		assert IGiftPurchaseAttempt.providedBy(purchase)
		
		try:
			index = self[username]
		except KeyError:
			index = UserGiftHistory()
			lifecycleevent.created(index)
			self[username] = index
			
		# register
		locate(purchase, index)
		IConnection(self).add(purchase)
		lifecycleevent.created(purchase)
		lifecycleevent.added(purchase)
		index.add(purchase)
		
		# set idens
		purchase.creator = username
		purchase.id = unicode(to_external_ntiid_oid(purchase))
		return purchase
	add = register_purchase
	
	def remove_purchase(self, username, purchase):
		assert IGiftPurchaseAttempt.providedBy(purchase)
		if username in self:
			index = self[username]
			if index.remove(purchase):
				lifecycleevent.removed(purchase) # remove iid
				locate(purchase, None)
				return True
		return False
	
	def get_pending_purchases(self, username, items=None):
		try:
			index = self[username]
			return list(index.get_pending_purchases(items))
		except KeyError:
			return ()
		
	def get_purchase_history(self, username, start_time=None, end_time=None):
		try:
			index = self[username]
			return list(index.get_history_by_time(start_time, end_time))
		except KeyError:
			return ()

def get_gift_registry(registry=component):
	result = registry.getUtility(IGiftRegistry)
	return result

def get_gift_purchase_attempt(purchase_id, username=None):
	result = find_object_with_ntiid(purchase_id)
	result = result if IGiftPurchaseAttempt.providedBy(result) else None
	if result is not None and username:
		result = None if result.creator != username else result
	return result

def remove_gift_purchase_attempt(purchase_id, username):
	purchase = get_gift_purchase_attempt(purchase_id, username)
	if purchase is not None and username:
		registry = get_gift_registry()
		result = registry.remove_purchase(username, purchase)
		return result
	return False

def get_gift_pending_purchases(username, items=None):
	registry = get_gift_registry()
	result = registry.get_pending_purchases(username, items)
	return result

def get_gift_purchase_history(username, start_time=None, end_time=None, catalog=None):
	intids = component.getUtility(zope.intid.IIntIds)
	catalog = get_catalog() if catalog is None else catalog
	creator_intids = catalog[IX_CREATOR].apply({'any_of': (username,)})
	time_ids = catalog[IX_CREATEDTIME].apply({'between': (start_time, end_time)})
	mimetype_intids = catalog[IX_MIMETYPE].apply({'any_of': GIFT_PURCHASE_ATTEMPT_MIME_TYPES})
	doc_ids = catalog.family.IF.intersection(time_ids, creator_intids)
	doc_ids = catalog.family.IF.intersection(doc_ids, mimetype_intids)
	result = LocatedExternalList(ResultSet(doc_ids, intids, ignore_invalid=True))
	return result

def register_gift_purchase_attempt(username, purchase):
	registry = get_gift_registry()
	result = registry.register_purchase(username, purchase)
	return result.id
