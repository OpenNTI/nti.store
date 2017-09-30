#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

generation = 12

from zope import component
from zope import interface

from zope.component.hooks import site as current_site

from zope.intid.interfaces import IIntIds

from nti.dataserver.interfaces import IDataserver
from nti.dataserver.interfaces import IOIDResolver

from nti.site.hostpolicy import get_all_host_sites

from nti.store.index import install_purchasable_catalog

from nti.store.interfaces import IPurchasable

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

        seen = set()
        lsm = ds_folder.getSiteManager()
        intids = lsm.getUtility(IIntIds)
        catalog = install_purchasable_catalog(ds_folder, intids)

        for current in get_all_host_sites():
            with current_site(current):
                for _, purchasable in list(component.getUtilitiesFor(IPurchasable)):
                    doc_id = intids.queryId(purchasable)
                    if doc_id is None or doc_id in seen:
                        continue
                    result += 1
                    seen.add(doc_id)
                    catalog.index_doc(doc_id, purchasable)

    component.getGlobalSiteManager().unregisterUtility(mock_ds, IDataserver)
    logger.info('Evolution %s done. %s record(s) indexed',
                generation, result)


def evolve(context):
    """
    Evolve to generation 12 by installing the purchasable index catalog
    """
    do_evolve(context, generation)
