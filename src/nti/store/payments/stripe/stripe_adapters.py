# -*- coding: utf-8 -*-
"""
Stripe purchase adapters.

$Id$
"""
from __future__ import print_function, unicode_literals, absolute_import
__docformat__ = "restructuredtext en"

import BTrees

from zope import component
from zope import interface
from zope.annotation import factory as an_factory
from zope.container import contained as zcontained

from persistent import Persistent

from nti.dataserver import interfaces as nti_interfaces

from nti.utils.property import alias

from . import interfaces as stripe_interfaces
from ... import interfaces as store_interfaces

@component.adapter(nti_interfaces.IUser)
@interface.implementer( stripe_interfaces.IStripeCustomer)
class _StripeCustomer(zcontained.Contained, Persistent):

	family = BTrees.family64

	CustomerID = None

	def __init__(self):
		self.Charges = self.family.OO.OOTreeSet()

	@property
	def id(self):
		return self.CustomerID

	def __contains__(self, charge):
		return  charge in self.Charges

	charges = alias('Charges')
	customer_id = alias('CustomerID')

_StripeCustomerFactory = an_factory(_StripeCustomer)

@component.adapter(store_interfaces.IPurchaseAttempt)
@interface.implementer(stripe_interfaces.IStripePurchase)
class _StripePurchase(zcontained.Contained, Persistent):

	TokenID = None
	ChargeID = None

	@property
	def purchase(self):
		return self.__parent__

	token_id = alias('TokenID')
	charge_id = alias('ChargeID')

_StripePurchaseFactory = an_factory(_StripePurchase)