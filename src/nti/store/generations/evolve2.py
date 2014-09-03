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

from ..interfaces import IPurchaseHistory
from ..interfaces import IEnrollmentAttempt
from ..purchase_history import PurchaseHistory

def update_user_purchase_data(user, intids=None):
	# check if user has purchase history
	annotations = IAnnotations(user)
	annotation_key = "%s.%s" % (PurchaseHistory.__module__, PurchaseHistory.__name__)
	if not annotation_key in annotations:
		return
		
	intids = intids or component.getUtility(zope.intid.IIntIds)
	
	update_count = 0
	removed_count = 0
	history = IPurchaseHistory(user)
	for p in list(history.values()):
		if IEnrollmentAttempt.providedBy(p):
			history.remove_purchase(p)	
			removed_count +=1
		else:
			p.id = to_external_ntiid_oid(p)
			update_count += 1
	
	return (update_count, removed_count) 

def evolve(context):
	"""
	Evolve generation 1 to 2 by either removing old 'enrollment'
	purchases and updating the __name__ property of them
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
				update_user_purchase_data(user, intids)
	