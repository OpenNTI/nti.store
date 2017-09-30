#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Store generation installation.

.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

generation = 12

from zope.generations.generations import SchemaManager

from zope.intid.interfaces import IIntIds

from nti.store.gift_registry import GiftRegistry

from nti.store.index import install_purchase_catalog
from nti.store.index import install_purchasable_catalog

from nti.store.interfaces import IGiftRegistry

logger = __import__('logging').getLogger(__name__)


class _StoreSchemaManager(SchemaManager):
    """
    A schema manager that we can register as a utility in ZCML.
    """

    def __init__(self):
        super(_StoreSchemaManager, self).__init__(
            generation=generation,
            minimum_generation=generation,
            package_name='nti.store.generations')


def install_catalogs(context):
    conn = context.connection
    root = conn.root()

    dataserver_folder = root['nti.dataserver']
    lsm = dataserver_folder.getSiteManager()
    intids = lsm.getUtility(IIntIds)

    install_purchase_catalog(dataserver_folder, intids)
    install_purchasable_catalog(dataserver_folder, intids)


def install_gift_registry(context):
    conn = context.connection
    root = conn.root()

    dataserver_folder = root['nti.dataserver']
    lsm = dataserver_folder.getSiteManager()
    intids = lsm.getUtility(IIntIds)

    registry = GiftRegistry()
    registry.__parent__ = dataserver_folder
    registry.__name__ = '++etc++store++giftregistry'
    intids.register(registry)
    lsm.registerUtility(registry, provided=IGiftRegistry)
    return registry


def evolve(context):
    install_catalogs(context)
    install_gift_registry(context)
