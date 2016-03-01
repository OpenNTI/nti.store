#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

generation = 8

from zope.catalog.interfaces import ICatalog

from zope.component.hooks import site, setHooks

from zope.intid.interfaces import IIntIds

from nti.store.purchase_index import IX_MIMETYPE
from nti.store.purchase_index import CATALOG_NAME

from nti.store.utils import PURCHASE_ATTEMPT_MIME_TYPES

from nti.zope_catalog.catalog import ResultSet

OLD_PID = u'tag:nextthought.com,2011-10:NTI-purchasable_course-LSTD_1153'
NEW_PID = u'tag:nextthought.com,2011-10:NTI-purchasable_course-Spring2015_LSTD_1153'

def get_purchases(catalog, intids):
	doc_ids = catalog[IX_MIMETYPE].apply({'any_of': PURCHASE_ATTEMPT_MIME_TYPES})
	result = ResultSet(doc_ids, intids, True)
	return result

def do_evolve(context, generation=generation):
	logger.info("Store evolution %s started", generation);

	count = 0
	setHooks()
	conn = context.connection
	ds_folder = conn.root()['nti.dataserver']
	
	with site(ds_folder):
		lsm = ds_folder.getSiteManager()
		intids = lsm.getUtility(IIntIds)
		catalog = lsm.queryUtility(ICatalog, name=CATALOG_NAME )
		for purchase in list(get_purchases(catalog, intids)): # we are mutating
			if OLD_PID not in purchase.Items:
				continue
			order = purchase.Order
			for item in order.Items:
				if item.NTIID == OLD_PID:
					item.NTIID = NEW_PID
					
			doc_id = intids.getId(purchase)
			catalog.index_doc(doc_id, purchase)
			count +=1
	
	logger.info('Store evolution %s done. %s items migrated', generation, count)

def evolve(context):
	"""
	Evolve to generation 8 by updating purchasable ids
	"""
	do_evolve(context)
