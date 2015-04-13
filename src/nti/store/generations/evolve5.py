#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

generation = 5

import zope.intid

from zope.catalog.interfaces import ICatalog

from nti.dataserver.metadata_index import CATALOG_NAME as METADATA_CATALOG_NAME

from nti.zope_catalog.catalog import ResultSet

from ..purchase_index import install_purchase_catalog

from ..utils import PURCHASE_ATTEMPT_MIME_TYPES

def do_evolve(context, generation=generation):
	logger.info("Store evolution %s started", generation);
	
	conn = context.connection
	dataserver_folder = conn.root()['nti.dataserver']
	lsm = dataserver_folder.getSiteManager()
	intids = lsm.getUtility(zope.intid.IIntIds)
	
	total = 0
	metadata_catalog = lsm.getUtility(ICatalog, METADATA_CATALOG_NAME)
	purchase_catalog = install_purchase_catalog(dataserver_folder, intids)
	
	mimetype_index = metadata_catalog['mimeType']
	item_intids = mimetype_index.apply({'any_of': PURCHASE_ATTEMPT_MIME_TYPES})
	results = ResultSet(item_intids, intids, True)
	for uid, obj in results.iter_pairs():
		try:
			purchase_catalog.index_doc(uid, obj)
			total += 1
		except Exception:
			logger.warn("Cannot index object with id %s", uid)
	
	logger.info('Store evolution %s done; %s items(s) indexed',
				generation, total)

def evolve(context):
	"""
	Evolve to generation 5 by registering purchase catalog
	"""
	do_evolve(context)
