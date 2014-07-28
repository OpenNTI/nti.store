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
from zope.annotation import interfaces as an_interfaces

from nti.externalization.persistence import NoPickle
from nti.externalization.externalization import WithRepr

from nti.schema.schema import EqHash
from nti.schema.field import SchemaConfigured
from nti.schema.fieldproperty import AdaptingFieldProperty
from nti.schema.fieldproperty import createDirectFieldProperties

from . import interfaces as store_interfaces

@interface.implementer(store_interfaces.IContentBundle,
					   an_interfaces.IAttributeAnnotatable)
@WithRepr
@NoPickle
@EqHash('NTIID')
class ContentBundle(SchemaConfigured):

	createDirectFieldProperties(store_interfaces.IContentBundle)
	Description = AdaptingFieldProperty(store_interfaces.IContentBundle['Description'])

	@property
	def id(self):
		return self.NTIID

	def __str__(self):
		return self.NTIID

