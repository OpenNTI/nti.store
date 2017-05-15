#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope.event import notify

from nti.store.content_roles import add_users_content_roles

from nti.store.interfaces import RedeemedPurchaseAttemptRegistered

from nti.store.purchase_attempt import create_redeemed_purchase_attempt

from nti.store.purchase_history import activate_items
from nti.store.purchase_history import register_purchase_attempt

from nti.store.purchasable import expand_purchase_item_ids


def make_redeem_purchase_attempt(user, original, code, activate_roles=True):
    # create and register a purchase attempt for accepting user
    redeemed = create_redeemed_purchase_attempt(original, code, original.Items)
    result = register_purchase_attempt(redeemed, user)
    activate_items(user, redeemed.Items)
    if activate_roles:
        lib_items = expand_purchase_item_ids(original.Items)
        add_users_content_roles(user, lib_items)
    notify(RedeemedPurchaseAttemptRegistered(redeemed, user, code))
    return result
