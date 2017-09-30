#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

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
