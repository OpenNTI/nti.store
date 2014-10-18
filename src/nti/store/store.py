#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from nti.ntiids.ntiids import find_object_with_ntiid

from . import get_user

from .interfaces import IPurchaseAttempt
from .interfaces import IGiftPurchaseAttempt

from .gift_registry import get_gift_pending_purchases

from .purchasable import get_all_purchasables

from .purchase_history import activate_items
from .purchase_history import deactivate_items
from .purchase_history import is_item_activated
from .purchase_history import get_pending_purchases

# rexport
activate_items = activate_items
deactivate_items = deactivate_items
is_item_activated = is_item_activated
get_all_purchasables = get_all_purchasables
get_pending_purchases = get_pending_purchases
get_gift_pending_purchases = get_gift_pending_purchases

def get_purchase_attempt(purchase_id, user=None):
    result = find_object_with_ntiid(purchase_id)
    result = result if IPurchaseAttempt.providedBy(result) else None
    if result is not None and user:
        if IPurchaseAttempt.providedBy(result):
            user = get_user(user)
            if user is not None:
                result = None if result.creator != user else result
        elif IGiftPurchaseAttempt.providedBy(result):
            username = getattr(user, 'username', user)
            result = None if result.creator != username.lower() else result
    return result
