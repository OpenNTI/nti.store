#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope.event import notify

from nti.store.interfaces import RedeemedPurchaseAttemptRegistered

from nti.store.purchase_attempt import create_redeemed_purchase_attempt

from nti.store.purchase_history import activate_items
from nti.store.purchase_history import register_purchase_attempt

logger = __import__('logging').getLogger(__name__)


def make_redeem_purchase_attempt(user, original, code):
    # create and register a purchase attempt for accepting user
    redeemed = create_redeemed_purchase_attempt(original, code, original.Items)
    result = register_purchase_attempt(redeemed, user)
    activate_items(user, redeemed.Items)
    notify(RedeemedPurchaseAttemptRegistered(redeemed, user, code))
    return result
