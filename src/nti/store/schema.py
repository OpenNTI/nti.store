#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division

__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope.schema.interfaces import InvalidValue

from nti.externalization.datetime import datetime_from_string

from nti.schema.field import ValidTextLine

class DateTime(ValidTextLine):

	def _validate(self, value):
		try:
			datetime_from_string(value)
		except Exception:
			raise InvalidValue('Invalid datetime', value, self.__name__)
		super(DateTime, self)._validate(value)
