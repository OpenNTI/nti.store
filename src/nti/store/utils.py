# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import re
import six
import sys

from nti.mimetype.mimetype import MIME_BASE

STORE_MIME_BASE = MIME_BASE + b'.store'

PURCHASE_ATTEMPT_MIME_TYPES = [MIME_BASE+x for x in (b'.purchaseattempt',
													 b'.invitationpurchaseattempt',
													 b'.redeemedpurchaseattempt',
													 b'.giftpurchaseattempt')]

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

# True if we are running on Python 3.
PY3 = sys.version_info[0] == 3

if PY3: # pragma: no cover
	def is_nonstr_iter(v):
		if isinstance(v, str):
			return False
		return hasattr(v, '__iter__')
else:
	def is_nonstr_iter(v):
		return hasattr(v, '__iter__')

# meta classes

class MetaStoreObject(type):

	def __new__(cls, name, bases, dct):
		t = type.__new__(cls, name, bases, dct)
		if not hasattr(cls, 'mimeType'):
			clazzname = getattr(cls, '__external_class_name__', name)
			clazzname = b'.' + clazzname.encode('ascii').lower()
			t.mime_type = t.mimeType = STORE_MIME_BASE + clazzname
		t.parameters = dict()
		return t
