#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import component
from zope import lifecycleevent

from zope.annotation import IAnnotations

from ZODB.interfaces import IConnection

from nti.ntiids.ntiids import find_object_with_ntiid

from nti.schema.interfaces import find_most_derived_interface

from nti.site.utils import registerUtility
from nti.site.utils import unregisterUtility

from nti.store import get_user

from nti.store.gift_registry import get_gift_registry
from nti.store.gift_registry import get_gift_purchase_history
from nti.store.gift_registry import get_gift_pending_purchases
from nti.store.gift_registry import remove_gift_purchase_attempt
from nti.store.gift_registry import register_gift_purchase_attempt

from nti.store.interfaces import IPurchasable
from nti.store.interfaces import IPurchaseAttempt
from nti.store.interfaces import IPurchaseHistory
from nti.store.interfaces import IGiftPurchaseAttempt

from nti.store.invitations import get_invitation_code
from nti.store.invitations import get_purchase_by_code

from nti.store.purchasable import get_purchasable
from nti.store.purchasable import get_purchasables

from nti.store.purchase_attempt import create_purchase_attempt
from nti.store.purchase_attempt import create_gift_purchase_attempt
from nti.store.purchase_attempt import get_purchasables as get_purchase_purchasables

from nti.store.purchase_history import PURCHASE_HISTORY_ANNOTATION_KEY

from nti.store.purchase_history import activate_items
from nti.store.purchase_history import deactivate_items
from nti.store.purchase_history import is_item_activated
from nti.store.purchase_history import has_history_by_item
from nti.store.purchase_history import get_pending_purchases
from nti.store.purchase_history import register_purchase_attempt
from nti.store.purchase_history import get_purchase_history_by_item
from nti.store.purchase_history import get_purchase_history as get_user_purchase_history
from nti.store.purchase_history import remove_purchase_attempt as remove_hist_purchase_attempt

from nti.store.redeem import make_redeem_purchase_attempt

logger = __import__('logging').getLogger(__name__)


# Purchasables


get_purchasable = get_purchasable
get_all_purchasables = get_purchasables


def register_purchasable(item, name=None, provided=None, registry=None):
    name = name or item.NTIID
    registry = registry if registry is not None else component.getSiteManager()
    if provided is None:
        provided = find_most_derived_interface(item, IPurchasable)
    if registry.queryUtility(provided, name=name) is None:
        registerUtility(registry, item, provided=provided, name=name)
        connection = IConnection(registry, None)
        if connection is not None:
            connection.add(item)
            lifecycleevent.added(item)
        return item
    return None


def remove_purchasable(item, provided=None, registry=None):
    name = getattr(item, 'NTIID', item)
    registry = registry if registry is not None else component.getSiteManager()
    if provided is None:
        if IPurchasable.providedBy(item):
            provided = find_most_derived_interface(item, IPurchasable)
        else:
            provided = IPurchasable
    result = unregisterUtility(registry,
                               name=name,
                               provided=provided)
    if IPurchasable.providedBy(item):
        lifecycleevent.removed(item)
        item.__parent__ = None  # ground
    return result


# Transaction codes


get_gift_code = get_invitation_code
get_transaction_code = get_invitation_code
get_purchase_by_code = get_purchase_by_code


# Item activation


activate_items = activate_items
deactivate_items = deactivate_items
is_item_activated = is_item_activated


# Purchase attempt

get_pending_purchases = get_pending_purchases
create_purchase_attempt = create_purchase_attempt
get_purchase_purchasables = get_purchase_purchasables
get_user_purchase_history = get_user_purchase_history
register_purchase_attempt = register_purchase_attempt
get_purchase_history_by_item = get_purchase_history_by_item


def get_purchase_attempt(purchase_id, user=None):
    result = find_object_with_ntiid(purchase_id) if purchase_id else None
    result = result if IPurchaseAttempt.providedBy(result) else None
    if result is not None and user:
        if IGiftPurchaseAttempt.providedBy(result):
            username = getattr(user, 'username', user)
            result = None if result.creator.lower() != username.lower() else result
        elif IPurchaseAttempt.providedBy(result):
            user = get_user(user)
            if user is not None:
                result = None if result.creator != user else result
    return result


def remove_purchase_attempt(purchase, user=None):
    if not IPurchaseAttempt.providedBy(purchase):
        purchase = get_purchase_attempt(purchase, user)

    # Order matters
    if IGiftPurchaseAttempt.providedBy(purchase):
        username = user or purchase.creator
        result = remove_gift_purchase_attempt(purchase, username)
    elif IPurchaseAttempt.providedBy(purchase):
        user = get_user(user or purchase.creator)
        result = remove_hist_purchase_attempt(purchase, user)
    else:
        result = False
    return result


# Gift registry


get_gift_registry = get_gift_registry
get_gift_purchase_history = get_gift_purchase_history
get_gift_pending_purchases = get_gift_pending_purchases
create_gift_purchase_attempt = create_gift_purchase_attempt
register_gift_purchase_attempt = register_gift_purchase_attempt


# Purchase history


has_history_by_item = has_history_by_item


def get_purchase_history(user, safe=True):
    if safe:
        result = IPurchaseHistory(user)
    else:
        annotations = IAnnotations(user)
        result = annotations.get(PURCHASE_HISTORY_ANNOTATION_KEY, None)
    return result


def delete_purchase_history(user):
    history = get_purchase_history(user, safe=False)
    if history is not None:
        history.clear()
        annotations = IAnnotations(user)
        annotations.pop(PURCHASE_HISTORY_ANNOTATION_KEY, None)
        return True
    return False


# Redeem


make_redeem_purchase_attempt = make_redeem_purchase_attempt
