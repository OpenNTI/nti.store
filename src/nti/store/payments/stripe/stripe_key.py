#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import base64

from Crypto.Cipher import XOR

from zope import interface

from zope.mimetype.interfaces import IContentTypeAware

from nti.externalization.representation import WithRepr

from nti.schema.schema import EqHash
from nti.schema.field import SchemaConfigured
from nti.schema.fieldproperty import createDirectFieldProperties

from nti.utils.property import alias as _

from ...utils import MetaStoreObject

from .interfaces import IStripeConnectKey

DEFAULT_PASSPHRASE = base64.b64decode('TjN4dFRoMHVnaHQhIUM=')

def make_ciphertext(plaintext, passphrase=DEFAULT_PASSPHRASE):
	cipher = XOR.new(passphrase)
	result = base64.b64encode(cipher.encrypt(plaintext))
	return result
	
def get_plaintext(ciphertext, passphrase=DEFAULT_PASSPHRASE):
	cipher = XOR.new(passphrase)
	result = cipher.decrypt(base64.b64decode(ciphertext))
	return result

@interface.implementer(IStripeConnectKey, IContentTypeAware)
@WithRepr
@EqHash('Alias',)
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
	