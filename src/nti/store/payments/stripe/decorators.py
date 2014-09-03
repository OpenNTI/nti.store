#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Stripe decorators

.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface
from zope import component

from nti.externalization.singleton import SingletonDecorator
from nti.externalization.interfaces import StandardExternalFields
from nti.externalization.interfaces import IExternalObjectDecorator

from ...decorators import PricedItemDecorator

from ...interfaces import IPurchaseAttempt

from . import STRIPE

from .interfaces import IStripePricedItem
from .interfaces import IStripePurchaseAttempt

LINKS = StandardExternalFields.LINKS

@component.adapter(IStripePricedItem)
@interface.implementer(IExternalObjectDecorator)
class StripePricedItemDecorator(PricedItemDecorator):
	pass

@component.adapter(IPurchaseAttempt)
@interface.implementer(IExternalObjectDecorator)
class PurchaseAttemptDecorator(object):

	__metaclass__ = SingletonDecorator

	def decorateExternalObject(self, original, external):
		if original.Processor == STRIPE:
			ps = IStripePurchaseAttempt(original)
			external['TokenID'] = ps.token_id
			external['ChargeID'] = ps.charge_id
