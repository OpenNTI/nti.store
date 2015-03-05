#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

generation = 2

import zope.intid

from zope import component
from zope.component.hooks import site, setHooks
from zope.annotation.interfaces import IAnnotations

from nti.dataserver.interfaces import IUser

from nti.externalization.oids import to_external_ntiid_oid

from ..interfaces import IPurchaseAttempt
from ..interfaces import IPurchaseHistory

from ..purchase_history import _check_valid
from ..purchase_history import PurchaseHistory

from nti.common.deprecated import hiding_warnings
with hiding_warnings():
	from ..interfaces import IEnrollmentAttempt
	
def _hard_removal(index, iid, intids):
	if iid is None:
		return False
	
	result = False
	
	# from item index
	for k, s in list(index.item_index.items()):
		if iid in s:
			s.remove(iid)
		if not s:
			index.item_index.pop(k, None)
			
	# from time index
	for k, v in list(index.time_index.items()):
		if v == iid:
			index.time_index.pop(k, None)
	
	# from purchase index
	if iid in index.purchases:
		index.purchases.remove(iid)
		result = True
		
	# unregister
	try:
		pa = intids.queryObject(iid)
		if IPurchaseAttempt.providedBy(pa):
			intids.forceUnregister(iid, pa, notify=False, removeAttribute=False)
			result = True
	except Exception as e:
		logger.warn("After hard removal; possibly leaking int-id %s. %s", iid, e)
	
	return result

def update_user_purchase_data(user, intids=None):	
	update_count = 0
	removed_count = 0
	
	# check if user has purchase history
	annotations = IAnnotations(user)
	annotation_key = "%s.%s" % (PurchaseHistory.__module__, PurchaseHistory.__name__)
	if not annotation_key in annotations:
		return (update_count, removed_count) 
		
	intids = intids or component.getUtility(zope.intid.IIntIds)
	history = IPurchaseHistory(user)
	if len(history) == 0: # no history remove
		del annotations[annotation_key]
		return (update_count, removed_count) 
		
	index = history.index
	for iid in list(index.purchases):
		p = intids.queryObject(iid)
		if _check_valid(p, iid, intids=intids, debug=False):
			if IEnrollmentAttempt.providedBy(p):
				history.remove_purchase(p)	
				removed_count +=1
			else:
				p.id = to_external_ntiid_oid(p)
				update_count += 1
		else:
			# attempt to remove broken objects
			queried = intids.queryId(p)
			if _hard_removal(index, iid, intids):
				removed_count += 1
			if _hard_removal(index, queried, intids):
				removed_count += 1

	history = IPurchaseHistory(user)
	if len(history) == 0: # no history remove
		del annotations[annotation_key]
	
	logger.debug("%s updated=%s, removed=%s", user, update_count, removed_count)
	return (update_count, removed_count) 

def evolve(context):
	"""
	Evolve generation 1 to 2 by either removing old 'enrollment'
	purchases and updating the __name__ property of them
	"""
	logger.info("Store generation %s started", generation)
	setHooks()
	conn = context.connection
	root = conn.root()
	ds_folder = root['nti.dataserver']
	with site(ds_folder):
		lsm = ds_folder.getSiteManager()
		intids = lsm.getUtility(zope.intid.IIntIds)
		users = ds_folder['users']
		for user in users.values():
			if IUser.providedBy(user):
				update_user_purchase_data(user, intids)
	logger.info("Store generation %s completed", generation)
	