# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import re
import six

from nti.mimetype.mimetype import MIME_BASE

from nti.store.interfaces import ICopier

#: Store MimeType base
STORE_MIME_BASE = MIME_BASE + '.store'

#: Purchase attempt mime type
PURCHASE_ATTEMPT_MIME_TYPE = \
    STORE_MIME_BASE + '.purchaseattempt'

#: Invitation purchase attempt
INVITATION_PURCHASE_ATTEMPT_MIME_TYPE = \
    STORE_MIME_BASE + '.invitationpurchaseattempt'

#: Redeem purchase attempt
REDEEM_PURCHASE_ATTEMPT_MIME_TYPE = STORE_MIME_BASE + '.redeemedpurchaseattempt'

#: Non-Gift purchase attempt MimeTypes
NONGIFT_PURCHASE_ATTEMPT_MIME_TYPES = \
    tuple([STORE_MIME_BASE + x for x in ('.purchaseattempt',
                                         '.invitationpurchaseattempt',
                                         '.redeemedpurchaseattempt')])

#: Gift purchase attempt MimeTypes
GIFT_PURCHASE_ATTEMPT_MIME_TYPES = \
    tuple([STORE_MIME_BASE + '.giftpurchaseattempt'])

#: Purchase attempt MimeTypes
PURCHASE_ATTEMPT_MIME_TYPES = \
    NONGIFT_PURCHASE_ATTEMPT_MIME_TYPES + GIFT_PURCHASE_ATTEMPT_MIME_TYPES


def from_delimited(value, delim='\s'):
    result = re.split(delim, value)
    result = re.findall(r"[^\s]+", value) if len(result) <= 1 else result
    return result


def to_collection(items=None, factory=list, delim='\s'):
    result = None
    if not items:
        result = factory()
    elif isinstance(items, factory):
        result = items
    elif isinstance(items, six.string_types):
        result = factory(from_delimited(items, delim))
    else:
        result = factory(items)
    return result


def to_set(items=None, delim='\s'):
    return to_collection(items, set, delim)


def to_list(items=None, delim='\s'):
    return to_collection(items, list, delim)


def to_frozenset(items=None, delim='\s'):
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
            clazzname = '.' + name.encode('ascii').lower()
            cls.mime_type = cls.mimeType = STORE_MIME_BASE + clazzname
            cls.parameters = dict()
        return cls
