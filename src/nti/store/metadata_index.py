#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import zope.intid

from zope import component
from zope import interface

from ZODB.interfaces import IBroken
from ZODB.POSException import POSError

from nti.dataserver.interfaces import IUser
from nti.dataserver.interfaces import ISystemUserPrincipal
from nti.dataserver.interfaces import IPrincipalMetadataObjectsIntIds

from .store import get_gift_registry
from .store import get_user_purchase_history

def get_uid(obj, intids=None):
	intids = component.getUtility(zope.intid.IIntIds) \
			 if intids is None else intids
	try:
		if IBroken.providedBy(obj):
			logger.warn("ignoring broken object %s", type(obj))
		else:
			uid = intids.queryId(obj)
			if uid is None:
				logger.warn("ignoring unregistered object %s", obj)
			else:
				return uid
	except (POSError):
		logger.error("ignoring broken object %s", type(obj))
	return None

@component.adapter(IUser)
@interface.implementer(IPrincipalMetadataObjectsIntIds)
class _PurchaseAttemptPrincipalObjectsIntIds(object):

	__slots__ = ('user',)

	def __init__(self, user):
		self.user = user

	def iter_intids(self):
		user = self.user
		intids = component.getUtility(zope.intid.IIntIds) 
		for purchase in get_user_purchase_history(user):
			uid = get_uid(purchase, intids=intids)
			if uid is not None:
				yield uid

@component.adapter(ISystemUserPrincipal)
@interface.implementer(IPrincipalMetadataObjectsIntIds)
class _GiftPurchaseAttemptPrincipalObjectsIntIds(object):

	__slots__ = ()
	
	def __init__(self, *args, **kwargs):
		pass

	def iter_intids(self, intids=None):
		registry = get_gift_registry()
		intids = component.getUtility(zope.intid.IIntIds) \
				 if intids is None else intids
		for username in registry.keys():
			for gift in registry.get_purchase_history(username):
				uid = get_uid(gift, intids=intids)
				if uid is not None:
					yield uid
