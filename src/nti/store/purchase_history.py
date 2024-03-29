#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Defines purchase history.

.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import BTrees

from persistent import Persistent

import six

from ZODB.interfaces import IConnection

from zope import component
from zope import interface
from zope import lifecycleevent

from zope.annotation import factory as an_factory

from zope.container.contained import Contained

from zope.deprecation import deprecated

from zope.intid.interfaces import IIntIds

from zope.location import locate

from zope.location.interfaces import ISublocations

from nti.base._compat import text_

from nti.dataserver.interfaces import IUser

from nti.externalization.interfaces import LocatedExternalList

from nti.ntiids.ntiids import find_object_with_ntiid

from nti.ntiids.oids import to_external_ntiid_oid

from nti.store import get_user

from nti.store.index import get_purchase_catalog

from nti.store.interfaces import PA_STATE_SUCCESS

from nti.store.interfaces import IPurchaseAttempt
from nti.store.interfaces import IPurchaseHistory

from nti.store.purchasable import get_purchasable
from nti.store.purchasable import get_purchasables

from nti.store.index import IX_SITE
from nti.store.index import IX_ITEMS
from nti.store.index import IX_STATE
from nti.store.index import IX_CREATOR
from nti.store.index import IX_MIMETYPE
from nti.store.index import IX_CREATEDTIME

from nti.store.utils import PURCHASE_ATTEMPT_MIME_TYPE
from nti.store.utils import NONGIFT_PURCHASE_ATTEMPT_MIME_TYPES as NONGIFT_MIME_TYPES

from nti.store.utils import to_frozenset

logger = __import__('logging').getLogger(__name__)


# classes


deprecated('_PurchaseIndex', 'Use new purchase storage')
class _PurchaseIndex(Persistent):
    pass


@component.adapter(IUser)
@interface.implementer(IPurchaseHistory, ISublocations)
class PurchaseHistory(Contained, Persistent):

    family = BTrees.family64

    def __init__(self):
        self.reset()

    def reset(self):
        # pylint: disable=no-member
        self._purchases = self.family.OO.OOBTree()
        self._items_activated = self.family.OO.OOTreeSet()

    @property
    def user(self):
        return self.__parent__

    @property
    def _intids(self):
        return component.getUtility(IIntIds)

    def activate_items(self, items):
        """
        register/activates the purchasables (NTIIDs)
        """
        items = to_frozenset(items)
        self._items_activated.update(items)

    def deactivate_items(self, items):
        """
        unregister the purchasables (NTIIDs)
        """
        count = 0
        items = to_frozenset(items)
        for item in items:
            if item in self._items_activated:
                count += 1
                self._items_activated.remove(item)
        return count

    def is_item_activated(self, item):
        return item in self._items_activated

    def add_purchase(self, purchase):
        # locate before firing events
        locate(purchase, self)
        # add to connection and fire event
        # pylint: disable=too-many-function-args
        IConnection(self).add(purchase)
        lifecycleevent.created(purchase)
        lifecycleevent.added(purchase)  # get an iid
        # now we can get an OID/NTIID
        result = purchase.id = text_(to_external_ntiid_oid(purchase))
        self._purchases[purchase.id] = purchase
        return result
    add = append = register_purchase = add_purchase

    def remove_purchase(self, purchase):
        try:
            pid = getattr(purchase, 'id', purchase)
            del self._purchases[pid]
            lifecycleevent.removed(purchase)  # remove iid
            result = True
        except KeyError:
            result = False
        return result
    remove = remove_purchase

    def get_purchase(self, pid):
        try:
            pid = getattr(pid, 'id', pid)
            result = self._purchases[pid]
        except KeyError:
            result = None
        return result
    get = get_purchasable

    def get_purchase_state(self, pid):
        p = self.get_purchase(pid)
        return p.State if p is not None else None

    def get_pending_purchases(self, items=None):
        items = to_frozenset(items) if items else None
        for p in self.values():
            if      (p.is_pending() or p.is_unknown()) \
                and (not items or to_frozenset(p.Items).intersection(items)):
                yield p

    def get_purchase_history_by_item(self, item):
        return get_purchase_history_by_item(self.user, item)

    def get_purchase_history(self, start_time=None, end_time=None):
        result = get_purchase_history(self.user, start_time, end_time)
        return iter(result)

    def has_history_by_item(self, purchasable_id):
        return has_history_by_item(self.user, purchasable_id)

    def clear(self):
        result = 0
        for p in list(self.values()):
            self.remove_purchase(p)
            result += 1
        return result

    def values(self):
        return self._purchases.values()

    def __iter__(self):
        return iter(self._purchases.values())

    def __len__(self):
        return len(self._purchases)

    def sublocations(self):
        for purchase in self.values():
            yield purchase

    def _v_check(self):
        import BTrees.check  # pylint: disable=redefined-outer-name
        for item in (self._items_activated, self._purchases):
            item._check()  # pylint: disable=protected-access
            BTrees.check.check(item)


PURCHASE_HISTORY_ANNOTATION_KEY = 'nti.store.purchase_history.PurchaseHistory'
_PurchaseHistoryFactory = an_factory(PurchaseHistory,
                                     PURCHASE_HISTORY_ANNOTATION_KEY)


# functions


def activate_items(user, items):
    user = get_user(user)
    if user is not None:
        hist = IPurchaseHistory(user)
        hist.activate_items(items)
        return True
    return False


def deactivate_items(user, items):
    user = get_user(user)
    if user is not None:
        hist = IPurchaseHistory(user)
        result = hist.deactivate_items(items)
        return result
    return None


def is_item_activated(user, item, site=None):
    user = get_user(user)
    catalog = get_purchase_catalog()
    query = {
        IX_CREATOR: {'any_of': (user.username,)},
        IX_STATE: {'any_of': (PA_STATE_SUCCESS,)},
        IX_MIMETYPE: {'any_of': (PURCHASE_ATTEMPT_MIME_TYPE,)},
    }
    if isinstance(site, six.string_types):
        sites = site.split()
        query[IX_SITE] = {'any_of': sites}
    if isinstance(item, six.string_types):
        items = item.split()
        query[IX_ITEMS] = {'any_of': items}
    doc_ids = catalog.apply(query) or ()
    return bool(doc_ids)


def get_purchase_attempt(purchase_id, user=None):
    result = find_object_with_ntiid(purchase_id)
    result = result if IPurchaseAttempt.providedBy(result) else None
    if result is not None and user:
        user = get_user(user)
        if user is not None:  # validate
            result = None if result.creator != user else result
    return result


def remove_purchase_attempt(purchase, user=None):
    user = get_user(user) or purchase.creator
    if user is not None:
        hist = IPurchaseHistory(user)
        hist.deactivate_items(purchase.Items)
        # pylint: disable=too-many-function-args
        result = hist.remove_purchase(purchase)
        return result
    return False


def get_pending_purchases(user, items=None):
    user = get_user(user)
    if user is not None:
        # pylint: disable=too-many-function-args
        hist = IPurchaseHistory(user)
        result = LocatedExternalList(hist.get_pending_purchases(items))
        return result
    return ()


def get_purchase_history(user, start_time=None, end_time=None, catalog=None):
    user = get_user(user)
    if user is None:
        result = ()
    else:
        intids = component.getUtility(IIntIds)
        catalog = get_purchase_catalog() if catalog is None else catalog
        query = {
            IX_CREATOR: {'any_of': (user.username,)},
            IX_MIMETYPE: {'any_of': NONGIFT_MIME_TYPES},
            IX_CREATEDTIME: {'between': (start_time, end_time)}
        }
        result = LocatedExternalList()
        for doc_id in catalog.apply(query) or ():
            obj = intids.queryObject(doc_id)
            if IPurchaseAttempt.providedBy(obj):
                result.append(obj)
    return result


def get_purchase_ids_by_items(user, *purchasables):
    catalog = get_purchase_catalog()
    query = {
        IX_ITEMS: {'any_of': purchasables},
        IX_CREATOR: {'any_of': (user.username,)},
        IX_MIMETYPE: {'any_of': NONGIFT_MIME_TYPES}
    }
    result = catalog.apply(query) or ()
    return result


def get_purchase_history_by_item(user, purchasable_id):
    user = get_user(user)
    if user is None:
        result = ()
    else:
        result = LocatedExternalList()
        intids = component.getUtility(IIntIds)
        doc_ids = get_purchase_ids_by_items(user, purchasable_id)
        for doc_id in doc_ids or ():
            obj = intids.queryObject(doc_id)
            if IPurchaseAttempt.providedBy(obj):
                result.append(obj)
    return result


def has_history_by_item(user, purchasable_id):
    user = get_user(user)
    if user is not None:
        doc_ids = get_purchase_ids_by_items(user, purchasable_id)
        return bool(doc_ids)
    return False


def register_purchase_attempt(purchase, user):
    user = get_user(user)
    if user is not None:
        hist = IPurchaseHistory(user)
        # pylint: disable=too-many-function-args
        hist.add_purchase(purchase)
        return purchase.id
    return None
add_purchase_attempt = register_purchase_attempt


def get_purchasable_ids(registry=component):
    result = LocatedExternalList(p.NTIID for p in get_purchasables(registry))
    return result
