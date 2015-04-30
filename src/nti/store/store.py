#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope.annotation import IAnnotations

from nti.ntiids.ntiids import find_object_with_ntiid

from . import get_user

from .interfaces import IPurchaseAttempt
from .interfaces import IPurchaseHistory
from .interfaces import IGiftPurchaseAttempt

from .gift_registry import get_gift_registry
from .gift_registry import get_gift_purchase_history
from .gift_registry import get_gift_pending_purchases
from .gift_registry import remove_gift_purchase_attempt
from .gift_registry import register_gift_purchase_attempt

from .invitations import get_invitation_code
from .invitations import get_purchase_by_code

from .purchasable import get_purchasable
from .purchasable import get_purchasables

from .purchase_history import PurchaseHistory

from .purchase_history import activate_items
from .purchase_history import deactivate_items
from .purchase_history import is_item_activated
from .purchase_history import has_history_by_item
from .purchase_history import get_pending_purchases
from .purchase_history import register_purchase_attempt
from .purchase_history import get_purchase_history_by_item
from .purchase_history import get_purchase_history as get_user_purchase_history
from .purchase_history import remove_purchase_attempt as remove_hist_purchase_attempt

from .purchase_attempt import create_purchase_attempt
from .purchase_attempt import create_gift_purchase_attempt
from .purchase_attempt import get_purchasables as get_purchase_purchasables

# rexport
get_purchasable = get_purchasable
get_all_purchasables = get_purchasables

get_gift_code = get_invitation_code
get_transaction_code = get_invitation_code
get_purchase_by_code = get_purchase_by_code

activate_items = activate_items
deactivate_items = deactivate_items
is_item_activated = is_item_activated
has_history_by_item = has_history_by_item
get_pending_purchases = get_pending_purchases
register_purchase_attempt = register_purchase_attempt
get_purchase_purchasables = get_purchase_purchasables
get_user_purchase_history = get_user_purchase_history
get_purchase_history_by_item = get_purchase_history_by_item

get_gift_registry = get_gift_registry
get_gift_purchase_history = get_gift_purchase_history
get_gift_pending_purchases = get_gift_pending_purchases
register_gift_purchase_attempt = register_gift_purchase_attempt

create_purchase_attempt = create_purchase_attempt
create_gift_purchase_attempt = create_gift_purchase_attempt


def get_purchase_attempt(purchase_id, user=None):
	result = find_object_with_ntiid(purchase_id) if purchase_id else None
	result = result if IPurchaseAttempt.providedBy(result) else None
	if result is not None and user:
		if IGiftPurchaseAttempt.providedBy(result):
			username = getattr(user, 'username', user)
			result = None if result.creator != username.lower() else result
		elif IPurchaseAttempt.providedBy(result):
			user = get_user(user)
			if user is not None:
				result = None if result.creator != user else result
	return result

def remove_purchase_attempt(purchase, user=None):
	if not IPurchaseAttempt.providedBy(purchase):
		purchase = get_purchase_attempt(purchase, user)
	
	if IGiftPurchaseAttempt.providedBy(purchase):
		username = user or purchase.creator
		result = remove_gift_purchase_attempt(purchase, username)
	elif IPurchaseAttempt.providedBy(purchase):
		user = get_user(user or purchase.creator)
		result = remove_hist_purchase_attempt(purchase, user)
	else:
		result = False
	return result

def get_purchase_history_annotation_key():
	annotation_key = "%s.%s" % (PurchaseHistory.__module__, PurchaseHistory.__name__)
	return annotation_key

def get_purchase_history(user, safe=True):
	if safe:
		result = IPurchaseHistory(user)
	else:
		annotations = IAnnotations(user)
		annotation_key = get_purchase_history_annotation_key()
		result = annotations.get(annotation_key, None)
	return result

def delete_purchase_history(user):
	history = get_purchase_history(user, safe=False)
	if history is not None:
		history.clear()
		annotations = IAnnotations(user)
		annotation_key = get_purchase_history_annotation_key()
		annotations.pop(annotation_key, None)
		return True
	return False
