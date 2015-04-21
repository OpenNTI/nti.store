#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

generation = 6

import zope.intid

from zope.catalog.interfaces import ICatalog

from zope.component.hooks import site, setHooks

from zope.annotation.interfaces import IAnnotations

from nti.dataserver.interfaces import IUser

from nti.zope_catalog.catalog import ResultSet

from ..purchase_index import IX_CREATOR
from ..purchase_index import IX_MIMETYPE
from ..purchase_index import CATALOG_NAME

from ..interfaces import IPurchaseHistory

from ..store import get_purchase_history_annotation_key

from ..utils import NONGIFT_PURCHASE_ATTEMPT_MIME_TYPES

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
		intids = lsm.getUtility(zope.intid.IIntIds)
		catalog = lsm.queryUtility(ICatalog, name=CATALOG_NAME )
		
		users = ds_folder['users']
		for user in users.values():
			if not IUser.providedBy(user):
				continue
			annotations = IAnnotations(user)
			if not annotation_key in annotations:
				continue
			history = IPurchaseHistory(user)

			if not hasattr(history, '_purchases'):
				history._purchases = history.family.OO.OOBTree()
			
			for purchase in get_purchases(catalog, user.username, intids):
				if not purchase.id in history._purchases:
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
