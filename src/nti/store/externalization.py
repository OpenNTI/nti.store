#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component
from zope import interface

from nti.externalization.interfaces import StandardExternalFields
from nti.externalization.interfaces import IInternalObjectExternalizer

from nti.externalization.datastructures import InterfaceObjectIO

from nti.store.interfaces import IPurchasable
from nti.store.interfaces import IPurchasableCourse
from nti.store.interfaces import IPurchasableChoiceBundle
from nti.store.interfaces import IPurchasableCourseChoiceBundle


@component.adapter(IPurchasable)
@interface.implementer(IInternalObjectExternalizer)
class _PurchasableSummaryExternalizer(object):

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


@component.adapter(IPurchasableChoiceBundle)
class _PurchasableChoiceBundleSummaryExternalizer(_PurchasableSummaryExternalizer):
    interface = IPurchasableChoiceBundle


@component.adapter(IPurchasableCourse)
class _PurchasableCourseSummaryExternalizer(_PurchasableSummaryExternalizer):

    fields_to_remove = _PurchasableSummaryExternalizer.fields_to_remove + \
                        ('Featured', 'Preview', 'StartDate', 'Department',
                         'Signature', 'Communities', 'Duration', 'EndDate')

    interface = IPurchasableCourse


@component.adapter(IPurchasableCourseChoiceBundle)
@interface.implementer(IInternalObjectExternalizer)
class _PurchasableCourseChoiceBundleSummaryExternalizer(_PurchasableCourseSummaryExternalizer):
    interface = IPurchasableCourseChoiceBundle
