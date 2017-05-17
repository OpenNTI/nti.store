#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from collections import MutableMapping

from zope import component
from zope import interface
from zope import lifecycleevent

from zope.container.contained import Contained

from zope.deprecation import deprecated

from zope.intid.interfaces import IIntIds

from ZODB.interfaces import IConnection

from persistent import Persistent

from nti.containers.containers import CaseInsensitiveCheckingLastModifiedBTreeContainer

from nti.externalization.interfaces import LocatedExternalList

from nti.externalization.oids import to_external_ntiid_oid

from nti.ntiids.ntiids import find_object_with_ntiid

from nti.property.property import alias

from nti.store import get_purchase_catalog

from nti.store.interfaces import IGiftRegistry
from nti.store.interfaces import IUserGiftHistory
from nti.store.interfaces import IGiftPurchaseAttempt

from nti.store.purchase_index import IX_CREATOR
from nti.store.purchase_index import IX_MIMETYPE
from nti.store.purchase_index import IX_CREATEDTIME

from nti.store.utils import GIFT_PURCHASE_ATTEMPT_MIME_TYPES

from nti.store.utils import to_frozenset

from nti.zope_catalog.catalog import ResultSet


deprecated('UserGiftHistory', 'Use new gift purchase storage')
@interface.implementer(IUserGiftHistory)
class UserGiftHistory(Contained, Persistent):
    pass


deprecated('GiftRecordMap', 'Use new gift purchase storage')
class GiftRecordMap(Persistent, MutableMapping, Contained):

    def __init__(self, username=None):
        dict.__init__(self)
        self.username = username


class GiftRecordContainer(CaseInsensitiveCheckingLastModifiedBTreeContainer,
                          Contained):

    username = alias('__name__')

    def append(self, value):
        key = to_external_ntiid_oid(value, use_cache=False)
        self[key] = value


@interface.implementer(IGiftRegistry)
class GiftRegistry(CaseInsensitiveCheckingLastModifiedBTreeContainer):

    def __init__(self):
        super(GiftRegistry, self).__init__()

    @property
    def Items(self):
        return dict(self)

    @property
    def intids(self):
        result = component.getUtility(IIntIds)
        return result

    def register_purchase(self, username, purchase):
        assert IGiftPurchaseAttempt.providedBy(purchase)
        try:
            index = self[username]
        except KeyError:
            index = GiftRecordContainer()
            self[username] = index
           
        purchase.creator = username
        IConnection(self).add(purchase)
        lifecycleevent.created(purchase) 
        index.append(purchase)
        return purchase
    add = append = add_purchase = register_purchase

    def remove_purchase(self, username, purchase):
        try:
            index = self[username]
            key = getattr(purchase, 'id', purchase)
            del index[key]
            return True
        except KeyError:
            return False
    remove = remove_purchase

    def get_purchases(self, username):
        try:
            index = self[username]
            return list(index.values())
        except KeyError:
            return ()

    def get_pending_purchases(self, username, items=None):
        result = []
        try:
            index = self[username]
            items = to_frozenset(items) if items else None
            for p in index.values():
                if      (p.is_pending() or p.is_unknown()) \
                    and (not items or to_frozenset(p.Items).intersection(items)):
                    result.append(p)
        except KeyError:
            pass
        return result or ()

    def get_purchase_history(self, username, start_time=None, end_time=None):
        result = get_gift_purchase_history(username, start_time, end_time)
        return result


def get_gift_registry(registry=component):
    result = registry.getUtility(IGiftRegistry)
    return result


def get_gift_purchase_attempt(purchase_id, username=None):
    result = find_object_with_ntiid(purchase_id)
    result = result if IGiftPurchaseAttempt.providedBy(result) else None
    if result is not None and username:
        result = None if result.creator != username else result
    return result


def remove_gift_purchase_attempt(purchase_id, username):
    purchase = get_gift_purchase_attempt(purchase_id, username)
    if purchase is not None and username:
        registry = get_gift_registry()
        result = registry.remove_purchase(username, purchase)
        return result
    return False


def get_gift_pending_purchases(username, items=None):
    registry = get_gift_registry()
    result = registry.get_pending_purchases(username, items)
    return result


def get_gift_purchase_history(username, start_time=None, end_time=None, catalog=None):
    intids = component.getUtility(IIntIds)
    catalog = get_purchase_catalog() if catalog is None else catalog
    query = {
        IX_CREATOR: {'any_of': (username,)},
        IX_CREATEDTIME: {'between': (start_time, end_time)},
        IX_MIMETYPE: {'any_of': GIFT_PURCHASE_ATTEMPT_MIME_TYPES}
    }
    doc_ids = catalog.apply(query) or ()
    return LocatedExternalList(ResultSet(doc_ids, intids, True))


def register_gift_purchase_attempt(username, purchase):
    registry = get_gift_registry()
    result = registry.register_purchase(username, purchase)
    return result.id
