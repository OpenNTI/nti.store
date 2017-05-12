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

from nti.externalization.singleton import SingletonDecorator
from nti.externalization.interfaces import IExternalObjectDecorator

from nti.ntiids.ntiids import get_provider

from nti.store.interfaces import IPurchasable

from nti.store.payments.interfaces import IConnectKey


@component.adapter(IPurchasable)
@interface.implementer(IExternalObjectDecorator)
class PurchasableDecorator(object):

    __metaclass__ = SingletonDecorator

    def decorateExternalObject(self, original, external):
        added = {}
        provider = get_provider(original.NTIID)
        for name, key in list(component.getUtilitiesFor(IConnectKey)):
            if name == provider:
                added[key.Processor] = key
        if added:
            payments = external.setdefault("Payments", {})
            payments.update(added)
