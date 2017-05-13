#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from functools import total_ordering

from zope import interface

from zope.mimetype.interfaces import IContentTypeAware

from zope.schema.fieldproperty import FieldPropertyStoredThroughField as FP

from nti.externalization.representation import WithRepr

from nti.schema.eqhash import EqHash

from nti.schema.field import SchemaConfigured

from nti.store.interfaces import IUserAddress
from nti.store.interfaces import IPaymentCharge

from nti.store.utils import MetaStoreObject


@WithRepr
@EqHash('Zip', 'City', 'State', 'Street', 'Country')
@interface.implementer(IUserAddress, IContentTypeAware)
class UserAddress(SchemaConfigured):

    __metaclass__ = MetaStoreObject

    Zip = FP(IUserAddress['Zip'])
    City = FP(IUserAddress['City'])
    State = FP(IUserAddress['State'])
    Street = FP(IUserAddress['Street'])
    Country = FP(IUserAddress['Country'])

    def __str__(self):
        return "%s\n%s,%s %s\n%s" % (self.Street,
                                     self.City,
                                     self.State,
                                     self.Zip,
                                     self.Country)

    @classmethod
    def create(cls, address_line1, address_line2=None, city=None, 
               state=None, zip_=None, country=None):
        city = city or u''
        zip_ = zip_ or IUserAddress['Zip'].default
        country = country or IUserAddress['Country'].default
        street = "%s\n%s" % (address_line1, address_line2 or u'')
        result = UserAddress(Street=street.strip(), 
                             City=city, State=state,
                             Zip=zip_, Country=country)
        return result


@WithRepr
@total_ordering
@EqHash('Name', 'Amount', 'Created', 'Currency')
@interface.implementer(IPaymentCharge, IContentTypeAware)
class PaymentCharge(SchemaConfigured):

    __metaclass__ = MetaStoreObject

    Name = FP(IPaymentCharge['Name'])
    Amount = FP(IPaymentCharge['Amount'])
    Address = FP(IPaymentCharge['Address'])
    Created = FP(IPaymentCharge['Created'])
    Currency = FP(IPaymentCharge['Currency'])
    CardLast4 = FP(IPaymentCharge['CardLast4'])
    
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
