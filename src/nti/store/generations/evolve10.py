#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

generation = 10

from zope import component
from zope import interface

from zope.component.hooks import site as current_site

from zope.intid.interfaces import IIntIds

from zope.location import locate

from nti.dataserver.interfaces import IDataserver
from nti.dataserver.interfaces import IOIDResolver

from nti.site.hostpolicy import get_host_site
from nti.site.hostpolicy import get_all_host_sites

from nti.store.interfaces import IPurchasable
from nti.store.interfaces import IPurchaseAttempt

from nti.store.purchase_index import IX_SITE
from nti.store.purchase_index import IX_ITEMS
from nti.store.purchase_index import SiteIndex
from nti.store.purchase_index import install_purchase_catalog


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


def index_site(doc_id, obj, items, site_index, seen):
    if len(items) == 1 and items[0] in seen:
        name = seen[items[0]]
        with current_site(get_host_site(name)):
            site_index.index_doc(doc_id, obj)
            return 1
    else:
        for site in get_all_host_sites():
            with current_site(site):
                for name in items:
                    purchasable = component.queryUtility(IPurchasable,
                                                         name=name)
                    if purchasable is not None:
                        site_index.index_doc(doc_id, obj)
                        return 1
    return 0


def do_evolve(context, generation=generation):
    conn = context.connection
    ds_folder = conn.root()['nti.dataserver']

    mock_ds = MockDataserver()
    mock_ds.root = ds_folder
    component.provideUtility(mock_ds, IDataserver)

    with current_site(ds_folder):
        assert component.getSiteManager() == ds_folder.getSiteManager(), \
               "Hooks not installed?"

        lsm = ds_folder.getSiteManager()
        intids = lsm.getUtility(IIntIds)

        result = 0
        seen = dict()
        catalog = install_purchase_catalog(ds_folder, intids)
        for name, clazz in ((IX_SITE, SiteIndex),):
            if name not in catalog:
                index = clazz(family=intids.family)
                intids.register(index)
                locate(index, catalog, name)
                catalog[name] = index
        site_index = catalog[IX_SITE]
        item_index = catalog[IX_ITEMS].index
        for doc_id in list(item_index.ids()):  # mutating
            obj = intids.queryObject(doc_id)
            items = index.documents_to_values.get(doc_id)
            if IPurchaseAttempt.providedBy(obj) and items:
                result += index_site(doc_id, obj, 
                                     list(items), site_index, seen)

    component.getGlobalSiteManager().unregisterUtility(mock_ds, IDataserver)
    logger.info('Evolution %s done. %s record(s) indexed',
                generation, result)


def evolve(context):
    """
    Evolve to generation 10 by adding site indexe to the purchase catalog
    """
    do_evolve(context, generation)
