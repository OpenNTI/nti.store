#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

generation = 6

from zope.annotation.interfaces import IAnnotations

from zope.catalog.interfaces import ICatalog

from zope.component.hooks import site
from zope.component.hooks import setHooks

from zope.intid.interfaces import IIntIds

from nti.dataserver.interfaces import IUser

from nti.store.interfaces import IPurchaseAttempt
from nti.store.interfaces import IPurchaseHistory

from nti.store.purchase_index import IX_CREATOR
from nti.store.purchase_index import IX_MIMETYPE
from nti.store.purchase_index import CATALOG_NAME

from nti.store.store import get_purchase_history_annotation_key

from nti.store.utils import NONGIFT_PURCHASE_ATTEMPT_MIME_TYPES

from nti.zope_catalog.catalog import ResultSet

def get_purchases(catalog, username, intids):
	creator_intids = catalog[IX_CREATOR].apply({'any_of': (username,)})
	mimetype_intids = catalog[IX_MIMETYPE].apply({'any_of': NONGIFT_PURCHASE_ATTEMPT_MIME_TYPES})
	doc_ids = catalog.family.IF.intersection(creator_intids, mimetype_intids)
	result = ResultSet(doc_ids, intids, True)
	return result

def do_evolve(context, generation=generation):
	logger.info("Store evolution %s started", generation);

	count = 0
	setHooks()
	conn = context.connection
	ds_folder = conn.root()['nti.dataserver']
	annotation_key = get_purchase_history_annotation_key()

	with site(ds_folder):
		lsm = ds_folder.getSiteManager()
		intids = lsm.getUtility(IIntIds)
		catalog = lsm.getUtility(ICatalog, name=CATALOG_NAME)

		users = ds_folder['users']
		for user in users.values():
			if not IUser.providedBy(user):
				continue
			annotations = IAnnotations(user)
			if not annotation_key in annotations:
				continue
			history = IPurchaseHistory(user)

			if hasattr(history, '_purchases'):
				continue

			history._purchases = history.family.OO.OOBTree()

			for purchase in get_purchases(catalog, user.username, intids):
				if 		IPurchaseAttempt.providedBy(purchase) \
					and not purchase.id in history._purchases:
					history._purchases[purchase.id] = purchase
					count += 1

			if hasattr(history, '_index'):
				del history._index

	logger.info('Store evolution %s done. %s items migrated', generation, count)

def evolve(context):
	"""
	Evolve to generation 6 by updating purchase storage
	"""
	do_evolve(context)
