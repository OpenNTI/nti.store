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

from .interfaces import IRedeemException
from .interfaces import IRefundException
from .interfaces import IPricingException
from .interfaces import IPurchaseException
from .interfaces import INTIStoreException

@interface.implementer(INTIStoreException)
class NTIStoreException(Exception):
	pass

class InvalidPurchasable(NTIStoreException):
	pass

@interface.implementer(IPricingException)
class PricingException(NTIStoreException):
	pass

@interface.implementer(IPurchaseException)
class PurchaseException(NTIStoreException):
	pass

@interface.implementer(IRefundException)
class RefundException(NTIStoreException):
	pass

@interface.implementer(IRedeemException)
class RedeemException(NTIStoreException):
	pass

def get_user(user):
	result = User.get_user(str(user)) if user and not IUser.providedBy(user) else user
	return result
