#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component
from zope import interface

from nti.externalization.interfaces import IExternalObjectDecorator

from nti.externalization.singleton import SingletonDecorator

from nti.store.decorators import PricedItemDecorator

from nti.store.interfaces import IPurchaseAttempt

from nti.store.payments.stripe import STRIPE

from nti.store.payments.stripe.interfaces import IStripePricedItem
from nti.store.payments.stripe.interfaces import IStripePurchaseAttempt


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
