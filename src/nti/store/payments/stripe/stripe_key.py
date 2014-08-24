#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from zope.mimetype.interfaces import IContentTypeAware

from nti.externalization.representation import WithRepr

from nti.schema.schema import EqHash
from nti.schema.field import SchemaConfigured
from nti.schema.fieldproperty import createDirectFieldProperties

from nti.utils.property import alias as _

from ...utils import MetaStoreObject

from .interfaces import IStripeConnectKey

@interface.implementer(IStripeConnectKey, IContentTypeAware)
@WithRepr
@EqHash('Alias',)
class StripeConnectKey(SchemaConfigured):
	createDirectFieldProperties(IStripeConnectKey)

	key = _('PrivateKey')
	alias = name = _('Alias')
	
	__metaclass__ = MetaStoreObject
