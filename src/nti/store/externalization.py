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

from nti.externalization.interfaces import StandardExternalFields
from nti.externalization.interfaces import IInternalObjectExternalizer

from nti.externalization.datastructures import InterfaceObjectIO

from nti.store.interfaces import IPurchasable
from nti.store.interfaces import IPurchasableChoiceBundle

logger = __import__('logging').getLogger(__name__)


@component.adapter(IPurchasable)
@interface.implementer(IInternalObjectExternalizer)
class PurchasableSummaryExternalizer(object):

    fields_to_remove = ('Icon', 'Thumbnail', 'License', 'Public', 'Description',
                        StandardExternalFields.CREATED_TIME,
                        StandardExternalFields.LAST_MODIFIED)

    interface = IPurchasable

    def __init__(self, obj):
        self.obj = obj

    def toExternalObject(self, **kwargs):
        result = InterfaceObjectIO(
                    self.obj, 
                    self.interface).toExternalObject(**kwargs)
        for name in self.fields_to_remove:
            result.pop(name, None)
        return result
_PurchasableSummaryExternalizer = PurchasableSummaryExternalizer


@component.adapter(IPurchasableChoiceBundle)
class _PurchasableChoiceBundleSummaryExternalizer(_PurchasableSummaryExternalizer):
    interface = IPurchasableChoiceBundle
