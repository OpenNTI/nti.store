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

from nti.store import PURCHASABLE
from nti.store import PURCHASABLE_COURSE
from nti.store import PURCHASABLE_CHOICE_BUNDLE
from nti.store import PURCHASABLE_COURSE_CHOICE_BUNDLE

from nti.store.interfaces import ICopier

#: Store MimeType base
STORE_MIME_BASE = MIME_BASE + b'.store'

#: Invitation purchase attempt
INVITATION_PURCHASE_ATTEMPT_MIME_TYPE = STORE_MIME_BASE + b'.invitationpurchaseattempt'

#: Redeem purchase attempt
REDEEM_PURCHASE_ATTEMPT_MIME_TYPE = STORE_MIME_BASE + b'.redeemedpurchaseattempt'

#: Non-Gift purchase attempt MimeTypes
NONGIFT_PURCHASE_ATTEMPT_MIME_TYPES = \
		tuple([STORE_MIME_BASE + x for x in (b'.purchaseattempt',
											 b'.invitationpurchaseattempt',
											 b'.redeemedpurchaseattempt') ])

#: Gift purchase attempt MimeTypes
GIFT_PURCHASE_ATTEMPT_MIME_TYPES = tuple([STORE_MIME_BASE + b'.giftpurchaseattempt'])

#: Purchase attempt MimeTypes
PURCHASE_ATTEMPT_MIME_TYPES = \
		NONGIFT_PURCHASE_ATTEMPT_MIME_TYPES + GIFT_PURCHASE_ATTEMPT_MIME_TYPES

#: Purchasables MimeTypes
PURCHASABLE_MIME_TYPES = []
PURCHASABLE_MIME_TYPES.append(STORE_MIME_BASE + b'.purchasable')
PURCHASABLE_MIME_TYPES.append(STORE_MIME_BASE + b'.purchasablecourse')
PURCHASABLE_MIME_TYPES.append(STORE_MIME_BASE + b'.purchasablechoicebundle')
PURCHASABLE_MIME_TYPES.append(STORE_MIME_BASE + b'.purchasablecoursechoicebundle')
PURCHASABLE_MIME_TYPES = tuple(PURCHASABLE_MIME_TYPES)

#: All store MimeTypes
ALL_STORE_MIME_TYPES = list(PURCHASE_ATTEMPT_MIME_TYPES)
ALL_STORE_MIME_TYPES.extend(PURCHASABLE_MIME_TYPES)
ALL_STORE_MIME_TYPES = tuple(ALL_STORE_MIME_TYPES)

def get_ntiid_type(mimeType):
	if mimeType == PURCHASABLE_MIME_TYPES[0]:  # purchasable
		return PURCHASABLE
	elif mimeType == PURCHASABLE_MIME_TYPES[1]:  # purchasable course
		return PURCHASABLE_COURSE
	elif mimeType == PURCHASABLE_CHOICE_BUNDLE[2]:  # purchasable choice bundle
		return PURCHASABLE_CHOICE_BUNDLE
	elif mimeType == PURCHASABLE_COURSE_CHOICE_BUNDLE[3]:  # purchasable course choice bundle
		return PURCHASABLE_COURSE_CHOICE_BUNDLE
	return None

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
