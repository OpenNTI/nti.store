# -*- coding: utf-8 -*-
"""
Stripe access key.

$Id$
"""

from __future__ import print_function, unicode_literals, absolute_import
__docformat__ = "restructuredtext en"

from zope import interface

from . import interfaces

@interface.implementer(interfaces.IStripeAccessKey)
class StripeAccessKey(object):

	__slots__ = ('alias', 'value')
	
	def __init__( self, alias, value):
		self.alias = alias
		self.value = value

	@property
	def name(self):
		return self.alias
	
	@property
	def key(self):
		return self.value
