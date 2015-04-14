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

def do_evolve(context, generation=generation):
	logger.info("Store evolution %s started", generation);
	
	conn = context.connection
	dataserver_folder = conn.root()['nti.dataserver']
	lsm = dataserver_folder.getSiteManager()
	lsm.getUtility(zope.intid.IIntIds)
	
	logger.info('Store evolution %s done; %s items(s) indexed',
				generation)

def evolve(context):
	"""
	Evolve to generation 5 by registering purchase catalog
	"""
	do_evolve(context)
