#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

generation = 11

from zope import component
from zope import interface

from zope.component.hooks import site as current_site

from zope.intid.interfaces import IIntIds

from zope.location import locate

from nti.dataserver.interfaces import IDataserver
from nti.dataserver.interfaces import IOIDResolver

from nti.store.gift_registry import get_gift_registry
from nti.store.gift_registry import GiftRecordContainer

logger = __import__('logging').getLogger(__name__)


@interface.implementer(IDataserver)
class MockDataserver(object):

    root = None

    def get_by_oid(self, oid, ignore_creator=False):
        resolver = component.queryUtility(IOIDResolver)
        if resolver is None:
            logger.warn("Using dataserver without a proper ISiteManager.")
        else:
            return resolver.get_object_by_oid(oid, ignore_creator=ignore_creator)
        return None


def do_evolve(context, generation=generation):
    conn = context.connection
    ds_folder = conn.root()['nti.dataserver']

    mock_ds = MockDataserver()
    mock_ds.root = ds_folder
    component.provideUtility(mock_ds, IDataserver)

    result = 0
    with current_site(ds_folder):
        assert component.getSiteManager() == ds_folder.getSiteManager(), \
               "Hooks not installed?"

        lsm = ds_folder.getSiteManager()
        intids = lsm.getUtility(IIntIds)
        registry = get_gift_registry()
        for username, old in tuple(registry.items()): # mutating
            if isinstance(old, GiftRecordContainer):
                continue
            intids.unregister(old)
            del registry[username]
            locate(old, None, None)
            # new container
            container = GiftRecordContainer()
            intids.register(container)
            registry[username] = container
            # move gift purchases
            for name, purchase in old.items():
                container._setitemf(name, purchase)
                result +=1
            old.clear()

    component.getGlobalSiteManager().unregisterUtility(mock_ds, IDataserver)
    logger.info('Evolution %s done. %s record(s) moved',
                generation, result)


def evolve(context):
    """
    Evolve to generation 11 by updating the user gift registry container
    """
    do_evolve(context, generation)
