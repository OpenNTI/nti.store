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

from nti.common.representation import WithRepr

from nti.schema.schema import EqHash
from nti.schema.field import SchemaConfigured
from nti.schema.fieldproperty import AdaptingFieldProperty
from nti.schema.fieldproperty import createDirectFieldProperties

from .interfaces import IItemBundle

@interface.implementer(IItemBundle, IAttributeAnnotatable)
@WithRepr
@EqHash('NTIID',)
class ItemBundle(SchemaConfigured):

	createDirectFieldProperties(IItemBundle)
	Description = AdaptingFieldProperty(IItemBundle['Description'])

	@property
	def id(self):
		return self.NTIID

	def __str__(self):
		return self.NTIID
ContentBundle = ItemBundle  # BWC
