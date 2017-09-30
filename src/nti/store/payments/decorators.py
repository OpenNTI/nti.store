#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import six

from zope import component
from zope import interface

from nti.externalization.interfaces import IExternalObjectDecorator

from nti.externalization.singleton import SingletonDecorator

from nti.store.interfaces import IPurchasable

from nti.store.payments.interfaces import IConnectKey

logger = __import__('logging').getLogger(__name__)


@six.add_metaclass(SingletonDecorator)
@component.adapter(IPurchasable)
@interface.implementer(IExternalObjectDecorator)
class PurchasableDecorator(object):

    def __init__(self, *args):
        pass

    def decorateExternalObject(self, original, external):
        added = {}
        provider = original.Provider
        for name, key in list(component.getUtilitiesFor(IConnectKey)):
            if name == provider:
                added[key.Processor] = key
        if added:
            payments = external.setdefault("Payments", {})
            payments.update(added)
