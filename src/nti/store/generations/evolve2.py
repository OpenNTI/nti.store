#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

generation = 2

from zope import component

from zope.annotation.interfaces import IAnnotations

from zope.component.hooks import site
from zope.component.hooks import setHooks

from zope.intid.interfaces import IIntIds

from nti.dataserver.interfaces import IUser

from nti.externalization.oids import to_external_ntiid_oid

from nti.store.interfaces import IPurchaseAttempt
from nti.store.interfaces import IPurchaseHistory

from nti.store.store import get_purchase_history_annotation_key

from nti.zope_catalog.catalog import isBroken

def _check_valid(p, uid, purchasable_id=None, intids=None, debug=True):
	if p is None or isBroken(p) or not IPurchaseAttempt.providedBy(p):
		return False
	# they exist in the backward index so that queryObject works,
	# but they do not actually have an intid that matches
	# (_ds_intid). This means that removal cannot work for
	# those cases that allow removal (courses). We think (hope) this is a
	# rare problem, so we pretend it doesn't exist, only logging loudly.
	# This could also be a corruption in our internal indexes.
	intids = component.getUtility(IIntIds) if intids is None else intids
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
	annotation_key = get_purchase_history_annotation_key()
	if not annotation_key in annotations:
		return (update_count, removed_count)

	intids = component.getUtility(IIntIds) if intids is None else intids
	history = IPurchaseHistory(user)
	if len(history) == 0:  # no history remove
		del annotations[annotation_key]
		return (update_count, removed_count)

	index = getattr(history, 'index', None)
	if index is not None:
		for iid in list(index.purchases):
			p = intids.queryObject(iid)
			if _check_valid(p, iid, intids=intids, debug=False):
				if IEnrollmentAttempt.providedBy(p):
					history.remove_purchase(p)
					removed_count += 1
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
	if len(history) == 0:  # no history remove
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
		intids = lsm.getUtility(IIntIds)
		users = ds_folder['users']
		for user in users.values():
			if IUser.providedBy(user):
				update_user_purchase_data(user, intids)
	logger.info("Store generation %s completed", generation)

from nti.common.deprecated import hiding_warnings
with hiding_warnings():
	from nti.store.interfaces import IEnrollmentAttempt
