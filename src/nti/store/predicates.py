#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import component

from nti.dataserver.interfaces import IUser
from nti.dataserver.interfaces import ISystemUserPrincipal

from nti.dataserver.metadata.predicates import BasePrincipalObjects

from nti.store.interfaces import IPurchaseHistory

from nti.store.store import get_gift_registry
from nti.store.store import get_all_purchasables

logger = __import__('logging').getLogger(__name__)


@component.adapter(IUser)
class _PurchaseAttemptPrincipalObjects(BasePrincipalObjects):

    def iter_objects(self):
        history = IPurchaseHistory(self.user)
        for purchase in history:
            yield purchase


@component.adapter(ISystemUserPrincipal)
class _PurchasablesPrincipalObjects(BasePrincipalObjects):

    def iter_objects(self):
        for purchasable in get_all_purchasables():
            yield purchasable


@component.adapter(ISystemUserPrincipal)
class _GiftPurchaseAttemptPrincipalObjects(BasePrincipalObjects):

    def iter_objects(self):
        registry = get_gift_registry()
        for username in registry.keys():
            for gift in registry.get_purchases(username):
                yield gift
