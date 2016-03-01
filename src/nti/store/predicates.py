#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component

from zope.component.hooks import site as current_site

from nti.dataserver.interfaces import IUser
from nti.dataserver.interfaces import ISystemUserPrincipal

from nti.metadata.predicates import BasePrincipalObjects

from nti.site.hostpolicy import get_all_host_sites

from nti.store.interfaces import IPurchaseHistory

from nti.store.store import get_gift_registry
from nti.store.store import get_all_purchasables

@component.adapter(IUser)
class _PurchaseAttemptPrincipalObjects(BasePrincipalObjects):

	def iter_objects(self):
		user = self.user
		history = IPurchaseHistory(user)
		for purchase in list(history):  # snapshot
			yield purchase

@component.adapter(ISystemUserPrincipal)
class _PurchasablesPrincipalObjects(BasePrincipalObjects):

	def iter_objects(self):
		seen = set()
		for site in get_all_host_sites():
			with current_site(site):
				for purchasable in get_all_purchasables():
					if purchasable.NTIID not in seen:
						seen.add(purchasable.NTIID)
						yield purchasable

@component.adapter(ISystemUserPrincipal)
class _GiftPurchaseAttemptPrincipalObjects(BasePrincipalObjects):

	def iter_objects(self, intids=None):
		registry = get_gift_registry()
		for username in list(registry.keys()):  # snapshot
			for gift in registry.get_purchases(username):
				yield gift
