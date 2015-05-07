#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import schema
from zope import component
from zope import interface

from nti.externalization.datastructures import InterfaceObjectIO
from nti.externalization.interfaces import IInternalObjectUpdater
from nti.externalization.interfaces import StandardExternalFields

from .utils import to_frozenset

from .interfaces import IPurchasable

ITEMS = StandardExternalFields.ITEMS

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

    def updateFromExternalObject(self, parsed, *args, **kwargs):
        remove_readonly_fields(parsed, IPurchasable)
        parsed[ITEMS] = to_frozenset(parsed.get(ITEMS))
        result = InterfaceObjectIO(self.obj, IPurchasable).updateFromExternalObject(parsed)
        return result
