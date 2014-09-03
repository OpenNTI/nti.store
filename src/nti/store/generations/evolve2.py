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

from ZODB.POSException import POSError

from nti.dataserver.interfaces import IUser

from ..interfaces import IPurchaseHistory
from ..interfaces import IEnrollmentAttempt
from ..purchase_history import PurchaseHistory

def remove_store_course_enrollment_data(user, intids=None):
	# check if user has purchase history
	annotations = IAnnotations(user)
	annotation_key = "%s.%s" % (PurchaseHistory.__module__, PurchaseHistory.__name__)
	if not annotation_key in annotations:
		return
		
	intids = intids or component.getUtility(zope.intid.IIntIds)
	
	count = 0
	history = IPurchaseHistory(user)
	for pa in list(history.values()):
		if IEnrollmentAttempt.providedBy(pa):
			try:
				history.remove_purchase(pa)
			except (POSError, KeyError):
				try:
					pa._p_activate()
				except KeyError:
					logger.exception("Broken object %r", pa)
					continue
					
				# let's try to do manually
				iid = None
				try:
					iid = intids.queryId(pa)
					history._removeFromIntIdIndex(iid)
				except:
					logger.exception("Could not remove from intid index %s/%r",
									 iid, pa)

				try:
					items = pa.Items
					history._removeFromItemIndex(items, iid)
				except:
					logger.exception("Could not remove from item index %s/%r",
									 iid, pa)
					
				try:
					startTime = pa.StartTime
					history._removeFromStartTimeIndex(startTime)
				except:
					logger.exception("Could not remove from time index %s/%r",
									 iid, pa)
					
				try:
					intids.unregister(pa)
				except:
					logger.error("Error while unregistering object %s/%r",
								 iid, pa)
				
			count +=1
	
	return count

def evolve(context):
	"""
	Evolve generation 1 to 2 by removing old enrollment data
	"""
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
				remove_store_course_enrollment_data(user, intids)
	