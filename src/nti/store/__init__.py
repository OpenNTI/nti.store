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

from nti.dataserver.interfaces import IUser

from nti.dataserver.users import User

from nti.store.interfaces import IRefundException
from nti.store.interfaces import IPricingException
from nti.store.interfaces import IPurchaseException
from nti.store.interfaces import INTIStoreException
from nti.store.interfaces import IRedemptionException

#: Pricing round decimal
ROUND_DECIMAL = 2

#: Purchasable NTIID type
PURCHASABLE = 'purchasable'

#: Purchasable course NTIID type
PURCHASABLE_COURSE = 'purchasable_course'

#: Purchasable content NTIID type
PURCHASABLE_CONTENT = 'purchasable_content'

#: Purchasable choice bundle NTIID type
PURCHASABLE_CHOICE_BUNDLE = 'purchasable_choice_bundle'

#: Purchasable course choice bundle NTIID type
PURCHASABLE_COURSE_CHOICE_BUNDLE = 'purchasable_course_choice_bundle'

#: Tuple of purchasable NTIID types
PURCHASABLE_NTIID_TYPES = (PURCHASABLE, PURCHASABLE_COURSE, PURCHASABLE_CONTENT, 
						   PURCHASABLE_CHOICE_BUNDLE, PURCHASABLE_COURSE_CHOICE_BUNDLE)

#: Purchases index name
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

def get_purchase_catalog():
	return component.getUtility(ICatalog, name=CATALOG_NAME)
get_catalog = get_purchase_catalog
