#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import schema
from zope import component
from zope import interface

from nti.externalization.datastructures import InterfaceObjectIO

from nti.externalization.interfaces import IInternalObjectUpdater
from nti.externalization.interfaces import StandardExternalFields

from nti.store.interfaces import IPurchasable

from nti.store.utils import to_frozenset

ITEMS = StandardExternalFields.ITEMS

logger = __import__('logging').getLogger(__name__)


def get_readonly_fields(iface):
    result = set()
    for name in schema.getFieldNames(iface):
        if iface[name].readonly:
            result.add(name)
    return result


def remove_readonly_fields(parsed, iface):
    for name in get_readonly_fields(iface):
        if name in parsed:
            del parsed[name]


@component.adapter(IPurchasable)
@interface.implementer(IInternalObjectUpdater)
class _PurchasableUpdater(object):

    __slots__ = ('obj',)

    def __init__(self, obj):
        self.obj = obj

    def updateFromExternalObject(self, parsed, *unused_args, **unused_kwargs):
        remove_readonly_fields(parsed, IPurchasable)
        parsed[ITEMS] = to_frozenset(parsed.get(ITEMS))
        result = InterfaceObjectIO(
                    self.obj, 
                    IPurchasable).updateFromExternalObject(parsed)
        return result
