#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import zope.i18nmessageid
MessageFactory = zope.i18nmessageid.MessageFactory('nti.dataserver')

from zope import interface

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
PURCHASABLE = u'purchasable'

#: Purchasable course NTIID type
PURCHASABLE_COURSE = u'purchasable_course'

#: Purchasable content NTIID type
PURCHASABLE_CONTENT = u'purchasable_content'

#: Purchasable choice bundle NTIID type
PURCHASABLE_CHOICE_BUNDLE = u'purchasable_choice_bundle'

#: Purchasable course choice bundle NTIID type
PURCHASABLE_COURSE_CHOICE_BUNDLE = u'purchasable_course_choice_bundle'

#: Tuple of purchasable NTIID types
PURCHASABLE_NTIID_TYPES = (PURCHASABLE,
                           PURCHASABLE_COURSE,
                           PURCHASABLE_CONTENT,
                           PURCHASABLE_CHOICE_BUNDLE,
                           PURCHASABLE_COURSE_CHOICE_BUNDLE)


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
    if user and not IUser.providedBy(user):
        result = User.get_user(str(user))
    else:
        result = user
    return result


# wait till module has been loaded to patch
from nti.store._patch import patch
patch()
del patch
