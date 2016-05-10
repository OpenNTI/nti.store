#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from nti.store.content_roles import add_users_content_roles

from nti.store.purchase_attempt import create_redeemed_purchase_attempt

from nti.store.purchase_history import activate_items
from nti.store.purchase_history import register_purchase_attempt

from nti.store.purchasable import expand_purchase_item_ids

def make_redeem_purchase_attempt(user, original, code, activate_roles=True):
	# create and register a purchase attempt for accepting user
	redeemed = create_redeemed_purchase_attempt(original, code)
	result = register_purchase_attempt(redeemed, user)
	activate_items(user, redeemed.Items)
	if activate_roles:
		lib_items = expand_purchase_item_ids(original.Items)
		add_users_content_roles(user, lib_items)
	return result
