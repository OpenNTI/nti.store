#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Defines purchase charge object.

.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import functools

from zope import interface
from zope.mimetype import interfaces as zmime_interfaces
from zope.schema.fieldproperty import FieldPropertyStoredThroughField as FP

from nti.externalization.externalization import WithRepr

from nti.schema.schema import EqHash
from nti.schema.field import SchemaConfigured

from . import utils
from . import interfaces as store_interfaces

@interface.implementer(store_interfaces.IUserAddress,
					   zmime_interfaces.IContentTypeAware)
@WithRepr
@EqHash('Zip', 'City', 'State', 'Street', 'Country')
class UserAddress(SchemaConfigured):

	__metaclass__ = utils.MetaStoreObject

	Street = FP(store_interfaces.IUserAddress['Street'])
	City = FP(store_interfaces.IUserAddress['City'])
	State = FP(store_interfaces.IUserAddress['State'])
	Zip = FP(store_interfaces.IUserAddress['Zip'])
	Country = FP(store_interfaces.IUserAddress['Country'])

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
		zip_ = zip_ or store_interfaces.IUserAddress['Zip'].default
		country = country or store_interfaces.IUserAddress['Country'].default
		street = "%s\n%s" % (address_line1, address_line2 or u'')
		result = UserAddress(Street=street.strip(), City=city, State=state,
							 Zip=zip_, Country=country)
		return result

@functools.total_ordering
@interface.implementer(store_interfaces.IPaymentCharge,
					   zmime_interfaces.IContentTypeAware)
@WithRepr
@EqHash('Name', 'Amount', 'Created', 'Currency')
class PaymentCharge(SchemaConfigured):

	__metaclass__ = utils.MetaStoreObject

	Amount = FP(store_interfaces.IPaymentCharge['Amount'])
	Currency = FP(store_interfaces.IPaymentCharge['Currency'])
	Created = FP(store_interfaces.IPaymentCharge['Created'])
	CardLast4 = FP(store_interfaces.IPaymentCharge['CardLast4'])
	Address = FP(store_interfaces.IPaymentCharge['Address'])
	Name = FP(store_interfaces.IPaymentCharge['Name'])

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

