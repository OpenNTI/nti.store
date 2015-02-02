#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

generation = 4

import zope.intid

from zope import component
from zope.component.hooks import site, setHooks

from nti.dataserver.interfaces import IUser

from nti.metadata import get_uid
from nti.metadata.interfaces import IMetadataQueue

from ..store import get_purchase_history
from ..predicates import _GiftPurchaseAttemptPrincipalObjects as gift_source

def do_evolve(context):
	setHooks()
	conn = context.connection
	root = conn.root()
	ds_folder = root['nti.dataserver']

	lsm = ds_folder.getSiteManager()
	intids = lsm.getUtility(zope.intid.IIntIds)
	
	queue = lsm.getUtility(IMetadataQueue)
	
	logger.info('Generation %s started', generation)
	
	gifts = purchases = 0
	with site(ds_folder):
		assert  component.getSiteManager() == ds_folder.getSiteManager(), \
				"Hooks not installed?"
	
		# purchase attempts
		users = ds_folder['users']
		for user in users.values():
			if not IUser.providedBy(user):
				continue
		
			# get all purchase attempt
			history = get_purchase_history(user, safe=False)
			if not history:
				continue

			for purchase in history.get_purchase_history():
				uid = get_uid(purchase, intids=intids)
				if uid is not None:
					try:
						queue.add(uid)
						purchases += 1
					except TypeError:
						pass

		# register gifts
		for uid in gift_source().iter_intids(intids=intids):
			try:
				queue.add(uid)
				gifts += 1
			except TypeError:
				pass
	
	logger.info('Generation %s completed. %s purchases(s) and %s gift(s) registered',
				generation, purchases, gifts)

def evolve(context):
	"""
	Evolve to generation 4 by registering purchase attempts w/ the metadata catalog
	"""
	do_evolve(context)
