#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface
from zope import component

from nti.externalization import interfaces as ext_interfaces
from nti.externalization.singleton import SingletonDecorator

from . import invitations
from . import interfaces as store_interfaces

LINKS = ext_interfaces.StandardExternalFields.LINKS

@component.adapter(store_interfaces.IPurchaseAttempt)
@interface.implementer(ext_interfaces.IExternalObjectDecorator)
class PurchaseAttemptDecorator(object):

	__metaclass__ = SingletonDecorator

	def decorateExternalObject(self, original, external):
		if store_interfaces.IInvitationPurchaseAttempt.providedBy(original):
			code = invitations.get_invitation_code(original)
			external['InvitationCode'] = code
			external['RemainingInvitations'] = original.tokens

@component.adapter(store_interfaces.IPricedItem)
@interface.implementer(ext_interfaces.IExternalObjectDecorator)
class PricedItemDecorator(object):

	__metaclass__ = SingletonDecorator

	def decorateExternalObject(self, original, external):
		non_dist_price = external.get('NonDiscountedPrice', None)
		if 'NonDiscountedPrice' in external and non_dist_price is None:
			del external['NonDiscountedPrice']
		external['Provider'] = original.Provider
		external['Amount'] = original.Amount
		external['Currency'] = original.Currency
