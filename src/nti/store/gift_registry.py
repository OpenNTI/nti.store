#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component
from zope import interface
from zope import lifecycleevent

from zope.container.contained import Contained

from zope.intid.interfaces import IIntIds

from ZODB.interfaces import IConnection

from nti.containers.containers import CaseInsensitiveCheckingLastModifiedBTreeContainer

from nti.externalization.interfaces import LocatedExternalList

from nti.externalization.oids import to_external_ntiid_oid

from nti.ntiids.ntiids import find_object_with_ntiid

from nti.property.property import alias

from nti.store.index import get_purchase_catalog

from nti.store.interfaces import IGiftRegistry
from nti.store.interfaces import IUserGiftHistory
from nti.store.interfaces import IGiftPurchaseAttempt

from nti.store.index import IX_CREATOR
from nti.store.index import IX_MIMETYPE
from nti.store.index import IX_CREATEDTIME

from nti.store.utils import GIFT_PURCHASE_ATTEMPT_MIME_TYPES

from nti.store.utils import to_frozenset


@interface.implementer(IUserGiftHistory)
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
        return get_gift_purchase_history(username, start_time, end_time)


def get_gift_registry(registry=component):
    return registry.getUtility(IGiftRegistry)


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
        return registry.remove_purchase(username, purchase)
    return False


def get_gift_pending_purchases(username, items=None):
    registry = get_gift_registry()
    return registry.get_pending_purchases(username, items)


def get_gift_purchase_history(username, start_time=None, end_time=None):
    catalog = get_purchase_catalog()
    intids = component.getUtility(IIntIds)
    query = {
        IX_CREATOR: {'any_of': (username,)},
        IX_CREATEDTIME: {'between': (start_time, end_time)},
        IX_MIMETYPE: {'any_of': GIFT_PURCHASE_ATTEMPT_MIME_TYPES}
    }
    result = LocatedExternalList()
    for doc_id in catalog.apply(query) or ():
        obj = intids.queryObject(doc_id)
        if IGiftPurchaseAttempt.providedBy(obj):
            result.append(obj)
    return result


def register_gift_purchase_attempt(username, purchase):
    registry = get_gift_registry()
    result = registry.register_purchase(username, purchase)
    return result.id
