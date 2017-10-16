#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import component
from zope import interface

from nti.externalization.interfaces import IExternalObjectDecorator

from nti.externalization.singleton import Singleton

from nti.store.decorators import PricedItemDecorator

from nti.store.interfaces import IPurchaseAttempt

from nti.store.payments.stripe import STRIPE

from nti.store.payments.stripe.interfaces import IStripePricedItem
from nti.store.payments.stripe.interfaces import IStripePurchaseAttempt

logger = __import__('logging').getLogger(__name__)


@component.adapter(IStripePricedItem)
@interface.implementer(IExternalObjectDecorator)
class StripePricedItemDecorator(PricedItemDecorator):
    pass


@component.adapter(IPurchaseAttempt)
@interface.implementer(IExternalObjectDecorator)
class PurchaseAttemptDecorator(Singleton):

    def decorateExternalObject(self, original, external):
        if original.Processor == STRIPE:
            ps = IStripePurchaseAttempt(original)
            external['TokenID'] = ps.TokenID
            external['ChargeID'] = ps.ChargeID
