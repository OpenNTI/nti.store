#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import zope.i18nmessageid
MessageFactory = zope.i18nmessageid.MessageFactory('nti.dataserver')

from zope import interface

from nti.dataserver.interfaces import IUser

from nti.dataserver.users.users import User

from nti.store.interfaces import IRefundException
from nti.store.interfaces import IPricingException
from nti.store.interfaces import IPurchaseException
from nti.store.interfaces import INTIStoreException
from nti.store.interfaces import IRedemptionException

#: Pricing round decimal
ROUND_DECIMAL = 2

#: Purchasable NTIID type
PURCHASABLE = u'purchasable'

#: Purchasable choice bundle NTIID type
PURCHASABLE_CHOICE_BUNDLE = u'purchasable_choice_bundle'


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
    return User.get_user(user)


# wait till module has been loaded to patch
from nti.store._patch import patch
patch()
del patch
