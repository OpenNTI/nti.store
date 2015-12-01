#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component
from zope import interface

from nti.externalization.singleton import SingletonDecorator
from nti.externalization.interfaces import IExternalObjectDecorator

from .store import get_gift_code
from .store import get_invitation_code
from .store import get_transaction_code

from .interfaces import IPricedItem
from .interfaces import IPurchaseAttempt
from .interfaces import IPurchasableCourse
from .interfaces import IGiftPurchaseAttempt
from .interfaces import IInvitationPurchaseAttempt

@component.adapter(IPurchaseAttempt)
@interface.implementer(IExternalObjectDecorator)
class PurchaseAttemptDecorator(object):

	__metaclass__ = SingletonDecorator

	def decorateExternalObject(self, original, external):
		code = get_transaction_code(original)
		external['TransactionID'] = code

@component.adapter(IInvitationPurchaseAttempt)
@interface.implementer(IExternalObjectDecorator)
class InvitationPurchaseAttemptDecorator(object):

	__metaclass__ = SingletonDecorator

	def decorateExternalObject(self, original, external):
		code = get_invitation_code(original)
		external['InvitationCode'] = code
		external['IsExpired'] = original.isExpired()
		external['Consumers'] = original.consumerMap
		external['RemainingInvitations'] = original.tokens

@component.adapter(IGiftPurchaseAttempt)
@interface.implementer(IExternalObjectDecorator)
class GiftPurchaseAttemptDecorator(object):

	__metaclass__ = SingletonDecorator

	def decorateExternalObject(self, original, external):
		code = get_gift_code(original)
		external['To'] = original.ReceiverName
		external['Sender'] = original.Creator
		if original.has_succeeded():
			external['RedemptionCode'] = external['GiftCode'] = code

@component.adapter(IPricedItem)
@interface.implementer(IExternalObjectDecorator)
class PricedItemDecorator(object):

	__metaclass__ = SingletonDecorator

	def decorateExternalObject(self, original, external):
		non_dist_price = external.get('NonDiscountedPrice', None)
		if 'NonDiscountedPrice' in external and non_dist_price is None:
			del external['NonDiscountedPrice']
		external['Provider'] = original.Provider
		external['Amount'] = original.Amount
		external['Currency'] = original.Currency

@component.adapter(IPurchasableCourse)
@interface.implementer(IExternalObjectDecorator)
class PurchasableCourseDecorator(object):

	__metaclass__ = SingletonDecorator

	def decorateExternalObject(self, original, external):
		# remove deprecated / legacy if no value is specified
		for name in ('Featured', 'Preview', 'StartDate', 'Department',
					 'Signature', 'Communities', 'Duration', 'EndDate'):
			value = external.get(name)
			if value is None:
				external.pop(name, None)
