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
from .gift_registry import register_gift_purchase_attempt

from .invitations import get_invitation_code
from .invitations import get_purchase_by_code

from .purchasable import get_purchasable
from .purchasable import get_all_purchasables

from .purchase_history import activate_items
from .purchase_history import deactivate_items
from .purchase_history import is_item_activated
from .purchase_history import get_pending_purchases
from .purchase_history import register_purchase_attempt

from .purchase_attempt import create_purchase_attempt
from .purchase_attempt import create_gift_purchase_attempt

# rexport
get_purchasable = get_purchasable
get_all_purchasables = get_all_purchasables

get_invitation_code = get_invitation_code
get_purchase_by_code = get_purchase_by_code

activate_items = activate_items
deactivate_items = deactivate_items
is_item_activated = is_item_activated
get_pending_purchases = get_pending_purchases
register_purchase_attempt = register_purchase_attempt

get_gift_pending_purchases = get_gift_pending_purchases
register_gift_purchase_attempt = register_gift_purchase_attempt

create_purchase_attempt = create_purchase_attempt
create_gift_purchase_attempt = create_gift_purchase_attempt

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