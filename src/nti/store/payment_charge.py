#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Defines purchase charge object.

.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from functools import total_ordering

from zope import interface
from zope.mimetype.interfaces import IContentTypeAware
from zope.schema.fieldproperty import FieldPropertyStoredThroughField as FP

from nti.externalization.representation import WithRepr

from nti.schema.schema import EqHash
from nti.schema.field import SchemaConfigured

from .utils import MetaStoreObject

from .interfaces import IUserAddress
from .interfaces import IPaymentCharge

@interface.implementer(IUserAddress, IContentTypeAware)
@WithRepr
@EqHash('Zip', 'City', 'State', 'Street', 'Country')
class UserAddress(SchemaConfigured):

	__metaclass__ = MetaStoreObject

	Street = FP(IUserAddress['Street'])
	City = FP(IUserAddress['City'])
	State = FP(IUserAddress['State'])
	Zip = FP(IUserAddress['Zip'])
	Country = FP(IUserAddress['Country'])

	def __str__(self):
		return "%s\n%s,%s %s\n%s" % (self.Street,
									 self.City,
									 self.State,
									 self.Zip,
									 self.Country)

	@classmethod
	def create(cls, address_line1, address_line2=None, city=None, state=None,
			   zip_=None, country=None):
		city = city or u''
		zip_ = zip_ or IUserAddress['Zip'].default
		country = country or IUserAddress['Country'].default
		street = "%s\n%s" % (address_line1, address_line2 or u'')
		result = UserAddress(Street=street.strip(), City=city, State=state,
							 Zip=zip_, Country=country)
		return result

@total_ordering
@interface.implementer(IPaymentCharge, IContentTypeAware)
@WithRepr
@EqHash('Name', 'Amount', 'Created', 'Currency')
class PaymentCharge(SchemaConfigured):

	__metaclass__ = MetaStoreObject

	Amount = FP(IPaymentCharge['Amount'])
	Currency = FP(IPaymentCharge['Currency'])
	Created = FP(IPaymentCharge['Created'])
	CardLast4 = FP(IPaymentCharge['CardLast4'])
	Address = FP(IPaymentCharge['Address'])
	Name = FP(IPaymentCharge['Name'])

	def __str__(self):
		return "%s:%s" % (self.Currency, self.Amount)

	def __lt__(self, other):
		try:
			return self.Created < other.Created
		except AttributeError:
			return NotImplemented

	def __gt__(self, other):
		try:
			return self.Created > other.Created
		except AttributeError:
			return NotImplemented

