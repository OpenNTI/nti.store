# -*- coding: utf-8 -*-
"""
Store utils module

.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import re
import six

from nti.mimetype.mimetype import nti_mimetype_with_class

def from_delimited(value, delim=' '):
	result = value.split(delim)
	result = re.findall("[^\s]+", value) if len(result) <= 1 else result
	return result

def to_collection(items=None, factory=list, delim=' '):
	result = None
	if not items:
		result = factory()
	elif isinstance(items, factory):
		result = items
	elif isinstance(items, six.string_types):
		result = factory(from_delimited(unicode(items), delim))
	else:
		result = factory(items)
	return result

def to_list(items=None, delim=' '):
	return to_collection(items, list)

def to_frozenset(items=None, delim=' '):
	return to_collection(items, frozenset, delim)

# meta classes

class MetaStoreObject(type):

	def __new__(cls, name, bases, dct):
		t = type.__new__(cls, name, bases, dct)
		clazzname = getattr(cls, '__external_class_name__', name)
		t.mimeType = nti_mimetype_with_class(clazzname)
		# legacy, deprecated
		t.mime_type = t.mimeType
		# IContentTypeAware
		t.parameters = dict()
		return t
