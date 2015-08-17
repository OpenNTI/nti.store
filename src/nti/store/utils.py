# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import re
import six

from nti.mimetype.mimetype import MIME_BASE

from .interfaces import ICopier

STORE_MIME_BASE = MIME_BASE + b'.store'

NONGIFT_PURCHASE_ATTEMPT_MIME_TYPES = \
		tuple([STORE_MIME_BASE + x for x in (b'.purchaseattempt',
											 b'.invitationpurchaseattempt',
											 b'.redeemedpurchaseattempt') ])

GIFT_PURCHASE_ATTEMPT_MIME_TYPES = tuple([STORE_MIME_BASE + b'.giftpurchaseattempt'])

PURCHASE_ATTEMPT_MIME_TYPES = \
		NONGIFT_PURCHASE_ATTEMPT_MIME_TYPES + GIFT_PURCHASE_ATTEMPT_MIME_TYPES

PURCHASABLE_ATTEMPT_MIME_TYPES = []
PURCHASABLE_ATTEMPT_MIME_TYPES.append(MIME_BASE + b'.purchasable')
PURCHASABLE_ATTEMPT_MIME_TYPES.append(MIME_BASE + b'.purchasablecourse')
PURCHASABLE_ATTEMPT_MIME_TYPES.append(MIME_BASE + b'.purchasablechoicebundle')
PURCHASABLE_ATTEMPT_MIME_TYPES.append(MIME_BASE + b'.purchasablecoursechoicebundle')
PURCHASABLE_ATTEMPT_MIME_TYPES = tuple(PURCHASABLE_ATTEMPT_MIME_TYPES)

ALL_STORE_MIME_TYPES = list(PURCHASE_ATTEMPT_MIME_TYPES)
ALL_STORE_MIME_TYPES.extend(PURCHASABLE_ATTEMPT_MIME_TYPES)
ALL_STORE_MIME_TYPES = tuple(ALL_STORE_MIME_TYPES)

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

def to_set(items=None, delim=' '):
	return to_collection(items, set, delim)

def to_list(items=None, delim=' '):
	return to_collection(items, list, delim)

def to_frozenset(items=None, delim=' '):
	return to_collection(items, frozenset, delim)

def copy_object(source, *args, **kwargs):
	copier = ICopier(source, None)
	if copier is not None:
		result = copier(source, *args, **kwargs)
	else:
		result = source.copy(*args, **kwargs)
	return result

# meta classes

class MetaStoreObject(type):

	def __new__(cls, name, bases, dct):
		cls = type.__new__(cls, name, bases, dct)
		ancestor = object
		for ancestor in cls.mro():
			if 'mimeType' in ancestor.__dict__:
				break
		if ancestor is not cls:
			clazzname = b'.' + name.encode('ascii').lower()
			cls.mime_type = cls.mimeType = STORE_MIME_BASE + clazzname
			cls.parameters = dict()
		return cls
