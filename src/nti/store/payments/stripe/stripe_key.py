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

from nti.common.property import alias as _

from nti.common.representation import WithRepr

from nti.schema.field import SchemaConfigured
from nti.schema.fieldproperty import createDirectFieldProperties

from nti.schema.schema import EqHash

from nti.store.payments.stripe.interfaces import IStripeConnectKey

from nti.store.utils import MetaStoreObject

from nti.utils.cypher import get_plaintext

@WithRepr
@EqHash('Alias',)
@interface.implementer(IStripeConnectKey, IContentTypeAware)
class StripeConnectKey(SchemaConfigured):
	createDirectFieldProperties(IStripeConnectKey)

	__metaclass__ = MetaStoreObject

	key = _('PrivateKey')
	alias = name = _('Alias')

	def __setattr__(self, name, value):
		if name in ("key", "PrivateKey", 'RefreshToken'):
			try:
				key = get_plaintext(value)
				value = unicode(key)
			except (TypeError, StandardError):
				pass
		return SchemaConfigured.__setattr__(self, name, value)
