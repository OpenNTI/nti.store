#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Defines content bundle object

.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from zope.annotation.interfaces import IAttributeAnnotatable

from nti.externalization.representation import WithRepr

from nti.property.property import alias

from nti.schema.eqhash import EqHash

from nti.schema.field import SchemaConfigured

from nti.schema.fieldproperty import AdaptingFieldProperty
from nti.schema.fieldproperty import createDirectFieldProperties

from nti.store.interfaces import IItemBundle


@WithRepr
@EqHash('NTIID',)
@interface.implementer(IItemBundle, IAttributeAnnotatable)
class ItemBundle(SchemaConfigured):
    createDirectFieldProperties(IItemBundle)

    Description = AdaptingFieldProperty(IItemBundle['Description'])

    id = ntiid = alias('NTIID')

    def __str__(self):
        return self.NTIID
ContentBundle = ItemBundle  # BWC
