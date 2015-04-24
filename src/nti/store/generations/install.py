#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Store generation installation.

.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

generation = 7

from zope.generations.generations import SchemaManager

import zope.intid

from ..interfaces import IGiftRegistry

from ..gift_registry import GiftRegistry

from ..purchase_index import install_purchase_catalog

class _StoreSchemaManager(SchemaManager):
	"""
	A schema manager that we can register as a utility in ZCML.
	"""
	def __init__(self):
		super(_StoreSchemaManager, self).__init__(
											generation=generation,
											minimum_generation=generation,
											package_name='nti.store.generations')

def evolve(context):
	install_catalog(context)
	install_gift_registry(context)
	
def install_catalog(context):
	conn = context.connection
	root = conn.root()
	dataserver_folder = root['nti.dataserver']
	lsm = dataserver_folder.getSiteManager()
	intids = lsm.getUtility(zope.intid.IIntIds)
	install_purchase_catalog(dataserver_folder, intids)
	
def install_gift_registry(context):
	conn = context.connection
	root = conn.root()

	dataserver_folder = root['nti.dataserver']
	lsm = dataserver_folder.getSiteManager()
	intids = lsm.getUtility(zope.intid.IIntIds)

	registry = GiftRegistry()
	registry.__parent__ = dataserver_folder
	registry.__name__ = '++etc++store++giftregistry'
	intids.register(registry)
	lsm.registerUtility(registry, provided=IGiftRegistry)

	return registry
