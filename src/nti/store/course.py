#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Defines course object and operations on them

.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import zope.deferredimport
zope.deferredimport.initialize()
zope.deferredimport.deprecated(
    "Use PurchasableCourse instead",
    Course='nti.app.products.courseware_store.model:PurchasableCourse')

zope.deferredimport.deprecatedFrom(
    "Moved to nti.app.products.courseware_store.model",
    "nti.app.products.courseware_store.model",
    "create_course",
    "PurchasableCourse",
    "PurchasableCourseChoiceBundle"
)
