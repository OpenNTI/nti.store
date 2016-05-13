#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

generation = 7

from zope.component.hooks import site
from zope.component.hooks import setHooks

from zope.intid.interfaces import IIntIds

from zope.location import locate

from nti.store.gift_registry import GiftRecordMap

from nti.store.interfaces import IGiftRegistry
from nti.store.interfaces import IUserGiftHistory

def do_evolve(context, generation=generation):
	logger.info("Store evolution %s started", generation);

	count = 0
	setHooks()
	conn = context.connection
	ds_folder = conn.root()['nti.dataserver']

	with site(ds_folder):
		lsm = ds_folder.getSiteManager()
		intids = lsm.getUtility(IIntIds)
		registry = lsm.getUtility(IGiftRegistry)

		for username, store in list(registry.items()): # mutating
			if not IUserGiftHistory.providedBy(store):
				continue

			index = GiftRecordMap(username)
			for iid in store.purchases:
				purchase = intids.queryObject(iid)
				if purchase is not None:
					count += 1
					purchase.__parent__ = index
					index[purchase.id] = purchase

			del registry[username]
			locate(store, None)

			registry[username] = index

	logger.info('Store evolution %s done. %s items migrated', generation, count)

def evolve(context):
	"""
	Evolve to generation 7 by updating gift registry storage
	"""
	do_evolve(context)
