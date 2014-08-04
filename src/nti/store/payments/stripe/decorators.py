#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Stripe decorators

.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import os

from zope import interface
from zope import component
from zope.container.interfaces import ILocation

from pyramid.threadlocal import get_current_request

from nti.dataserver.links import Link

from nti.externalization.singleton import SingletonDecorator
from nti.externalization.externalization import toExternalObject
from nti.externalization.interfaces import StandardExternalFields
from nti.externalization.interfaces import IExternalObjectDecorator

from ...decorators import PricedItemDecorator

from ...interfaces import IPurchasable

from .interfaces import IStripeConnectKey
from .interfaces import IStripePricedItem

LINKS = StandardExternalFields.LINKS

@component.adapter(IStripePricedItem)
@interface.implementer(IExternalObjectDecorator)
class StripePricedItemDecorator(PricedItemDecorator):
	pass

@component.adapter(IPurchasable)
@interface.implementer(IExternalObjectDecorator)
class PurchasableDecorator(object):

	__metaclass__ = SingletonDecorator

	def set_links(self, original, external):
		request = get_current_request()
		if original.Amount and request:
			_ds_path = os.path.split(request.current_route_path())[0]
			price_href = _ds_path + '/price_purchasable_with_stripe_coupon'
			link = Link(price_href, rel="price_with_stripe_coupon", method='Post')
			interface.alsoProvides(link, ILocation)
			external.setdefault(LINKS, []).append(link)

	def decorateExternalObject(self, original, external):
		keyname = original.Provider
		result = component.queryUtility(IStripeConnectKey, keyname)
		if result:
			external['StripeConnectKey'] = toExternalObject(result)
		self.set_links(original, external)
