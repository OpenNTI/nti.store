#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import six

from zope import component
from zope import interface

from nti.externalization.interfaces import IExternalObjectDecorator

from nti.externalization.singleton import SingletonDecorator

from nti.store.interfaces import IPricedItem
from nti.store.interfaces import IPurchaseAttempt
from nti.store.interfaces import IGiftPurchaseAttempt
from nti.store.interfaces import IInvitationPurchaseAttempt

from nti.store.store import get_gift_code
from nti.store.store import get_invitation_code
from nti.store.store import get_transaction_code

logger = __import__('logging').getLogger(__name__)


@six.add_metaclass(SingletonDecorator)
@component.adapter(IPurchaseAttempt)
@interface.implementer(IExternalObjectDecorator)
class PurchaseAttemptDecorator(object):

    def __init__(self, *args):
        pass

    def decorateExternalObject(self, original, external):
        code = get_transaction_code(original)
        external['TransactionID'] = code


@six.add_metaclass(SingletonDecorator)
@component.adapter(IInvitationPurchaseAttempt)
@interface.implementer(IExternalObjectDecorator)
class InvitationPurchaseAttemptDecorator(object):

    def __init__(self, *args):
        pass

    def decorateExternalObject(self, original, external):
        code = get_invitation_code(original)
        external['InvitationCode'] = code
        external['IsExpired'] = original.isExpired()
        external['Consumers'] = original.consumerMap
        external['RemainingInvitations'] = original.tokens


@six.add_metaclass(SingletonDecorator)
@component.adapter(IGiftPurchaseAttempt)
@interface.implementer(IExternalObjectDecorator)
class GiftPurchaseAttemptDecorator(object):

    def __init__(self, *args):
        pass

    def decorateExternalObject(self, original, external):
        code = get_gift_code(original)
        external['To'] = original.ReceiverName
        external['Sender'] = original.Creator
        if original.has_succeeded():
            external['RedemptionCode'] = external['GiftCode'] = code


@six.add_metaclass(SingletonDecorator)
@component.adapter(IPricedItem)
@interface.implementer(IExternalObjectDecorator)
class PricedItemDecorator(object):

    def __init__(self, *args):
        pass

    def decorateExternalObject(self, original, external):
        non_dist_price = external.get('NonDiscountedPrice', None)
        if 'NonDiscountedPrice' in external and non_dist_price is None:
            del external['NonDiscountedPrice']
        external['Provider'] = original.Provider
        external['Amount'] = original.Amount
        external['Currency'] = original.Currency
