#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Defines purchasable object and operations on them

.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from nti.ntiids.interfaces import INTIIDResolver

from .purchasable import get_purchasable

@interface.implementer(INTIIDResolver)
class _PurchasableResolver(object):

	singleton = None

	def __new__(cls, *args, **kwargs):
		if not cls.singleton:
			cls.singleton = super(_PurchasableResolver, cls).__new__(cls)
		return cls.singleton

	def resolve(self, ntiid_string):
		return get_purchasable(ntiid_string)

_CourseResolver = _PurchasableResolver  # alias BWC
