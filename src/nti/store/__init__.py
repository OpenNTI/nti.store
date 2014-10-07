#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import zope.i18nmessageid
MessageFactory = zope.i18nmessageid.MessageFactory('nti.dataserver')

from zope import interface

from nti.dataserver.users import User
from nti.dataserver.interfaces import IUser

from .interfaces import INTIStoreException

@interface.implementer(INTIStoreException)
class NTIStoreException(Exception):
    pass

class InvalidPurchasable(NTIStoreException):
    pass

class PricingException(NTIStoreException):
    pass

def get_user(user):
    if user is not None:
        result = User.get_user(str(user)) if not IUser.providedBy(user) else user
        return result
    return None

