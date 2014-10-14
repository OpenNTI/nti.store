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

from nti.dataserver.interfaces import ACE_DENY_ALL
from nti.dataserver.interfaces import ALL_PERMISSIONS
from nti.dataserver.containers import CaseInsensitiveCheckingLastModifiedBTreeContainer

from nti.dataserver.authorization import ROLE_ADMIN
from nti.dataserver.authorization_acl import ace_allowing
from nti.dataserver.authorization_acl import acl_from_aces

from nti.externalization.oids import to_external_ntiid_oid

from nti.ntiids.ntiids import find_object_with_ntiid

from nti.utils.property import Lazy

from nti.zodb.containers import time_to_64bit_int

from .utils import to_frozenset

from .interfaces import IGiftRegistry
from .interfaces import IUserGiftIndex
from .interfaces import IUserGiftHistory
from .interfaces import IGiftPurchaseAttempt

@interface.implementer(IUserGiftIndex)
class UserGiftIndex(Contained, Persistent):

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

	def get_pending_purchase_for(self, items=None):
		items = to_frozenset(items) if items else None
		for p in self.values():
			if 	(p.is_pending() or p.is_unknown()) and \
				(not items or p.Items.intersection(items)):
				return p
		return None
	
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
		aces = [ace_allowing(ROLE_ADMIN, ALL_PERMISSIONS, UserGiftIndex)]
		creator = self.creator
		if creator is not None:
			aces.append(ace_allowing(creator, ALL_PERMISSIONS, UserGiftIndex))
		aces.append(ACE_DENY_ALL)
		return acl_from_aces(aces)

@interface.implementer(IUserGiftHistory)
class UserGiftHistory(CaseInsensitiveCheckingLastModifiedBTreeContainer):

	@property
	def Items(self):
		return dict(self)
	
	def register_purchase(self, username, purchase):
		assert IGiftPurchaseAttempt.providedBy(purchase)
		
		try:
			index = self[username]
		except KeyError:
			index = UserGiftIndex()
			lifecycleevent.created(index)
			self[username] = index
			
		locate(purchase, index)
		IConnection(self).add(purchase)
		lifecycleevent.created(purchase)
		lifecycleevent.added(purchase)  # get an iid
		index.add(purchase)
		# set id/name
		purchase.creator = username
		purchase.id = unicode(to_external_ntiid_oid(purchase))
		return purchase
	add = register_purchase
	
	def get_pending_purchase_for(self, username, items=None):
		pass
		
	@property
	def __acl__(self):
		aces = [ace_allowing(ROLE_ADMIN, ALL_PERMISSIONS, UserGiftHistory)]
		aces.append(ACE_DENY_ALL)
		return acl_from_aces(aces)

@interface.implementer(IGiftRegistry)
class GiftRegistry(Contained, Persistent):
	
	def __init__(self):
		self._history = UserGiftHistory()

	def recordPurchase(self, username, purchase):
		return self._history.recordPurchase(username, purchase)
	add = recordPurchase

def get_gift_purchase_attempt(purchase_id, username=None):
	result = find_object_with_ntiid(purchase_id)
	if IGiftPurchaseAttempt.providedBy(result) and username:
		result = None if result.creator != username else result
	return result

# def get_pending_purchases(username):
# 	user = get_user(user)
# 	if user is not None:
# 		hist = IPurchaseHistory(user)
# 		result = LocatedExternalList(hist.get_pending_purchases())
# 		return result
# 	return ()

# def get_purchase_history(user, start_time=None, end_time=None):
# 	user = get_user(user)
# 	if user is not None:
# 		hist = IPurchaseHistory(user)
# 		result = LocatedExternalList(hist.get_purchase_history(start_time, end_time))
# 		return result
# 	return ()
# 
# def has_history_by_item(user, purchasable_id):
# 	user = get_user(user)
# 	if user is not None:
# 		hist = IPurchaseHistory(user)
# 		result = hist.has_history_by_item(purchasable_id)
# 		return result
# 	return False
# 
# def get_purchase_history_by_item(user, purchasable_id):
# 	user = get_user(user)
# 	if user is not None:
# 		hist = IPurchaseHistory(user)
# 		result = LocatedExternalList(hist.get_purchase_history_by_item(purchasable_id))
# 		return result
# 	return ()
# 
# def get_pending_purchase_for(user, items):
# 	user = get_user(user)
# 	if user is not None:
# 		hist = IPurchaseHistory(user)
# 		result = hist.get_pending_purchase_for(items)
# 		return result
# 	return ()
# 
# def register_purchase_attempt(purchase, user):
# 	user = get_user(user)
# 	if user is not None:
# 		hist = IPurchaseHistory(user)
# 		hist.register_purchase(purchase)
# 		return purchase.id
# 	return None
