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

from zope import component
from zope import interface

from zope.catalog.interfaces import ICatalog

from nti.dataserver.users import User
from nti.dataserver.interfaces import IUser

from .interfaces import IRefundException
from .interfaces import IPricingException
from .interfaces import IPurchaseException
from .interfaces import INTIStoreException
from .interfaces import IRedemptionException

ROUND_DECIMAL = 2
PURCHASABLE = 'purchasable'
PURCHASABLE_COURSE = 'purchasable_course'
PURCHASABLE_CONTENT = 'purchasable_content'
PURCHASABLE_CHOICE_BUNDLE = 'purchasable_choice_bundle'
PURCHASABLE_COURSE_CHOICE_BUNDLE = 'purchasable_course_choice_bundle'

CATALOG_NAME = 'nti.dataserver.++etc++purchase-catalog'

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

@interface.implementer(IRedemptionException)
class RedemptionException(NTIStoreException):
	pass

def get_user(user):
	result = User.get_user(str(user)) if user and not IUser.providedBy(user) else user
	return result

def get_catalog():
	return component.getUtility(ICatalog, name=CATALOG_NAME)
