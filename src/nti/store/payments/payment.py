# -*- coding: utf-8 -*-
"""
Defines payment.

$Id: purchasable.py 18394 2013-04-18 19:27:11Z carlos.sanchez $
"""
from __future__ import print_function, unicode_literals, absolute_import
__docformat__ = "restructuredtext en"

from zope import interface
from zope.cachedescriptors.property import Lazy
from zope.mimetype import interfaces as zmime_interfaces
from zope.schema.fieldproperty import FieldPropertyStoredThroughField as FP

from nti.utils.schema import SchemaConfigured

from ..purchasable import get_purchasable
from . import interfaces as pay_interfaces
from ..utils import MetaStoreObject, to_frozenset

@interface.implementer(pay_interfaces.IPayment, zmime_interfaces.IContentTypeAware)
class Payment(SchemaConfigured):

	__metaclass__ = MetaStoreObject

	Items = FP(pay_interfaces.IPayment['Items'])
	Description = FP(pay_interfaces.IPayment['Description'])
	ExpectedAmount = FP(pay_interfaces.IPayment['ExpectedAmount'])
	ExpectedCurrency = FP(pay_interfaces.IPayment['ExpectedCurrency'])

	@Lazy
	def purchasables(self):
		result = []
		for item in self.Items:
			p = get_purchasable(item)
			if p is not None:
				result.append(p)
		return result

	def __getitem__(self, index):
		return self.purchasables[index]

	def __iter__(self):
		return iter(self.purchasables)

	def __str__(self):
		return "%s,%s" % (self.Items, self.Description)

	def __repr__(self):
		return "%s(%s,%s,%s,%s)" % (self.__class__.__name__, self.Items, self.Description,
									self.ExpectedAmount, self.ExpectedCurrency)

	def __eq__(self, other):
		try:
			return self is other or (self.Items == other.Items)
		except AttributeError:
			return NotImplemented

	def __hash__(self):
		xhash = 47
		xhash ^= hash(self.Items)
		return xhash

def create_payment(items, description, amount=None, currency='USD'):
	items = to_frozenset(items)
	currency = currency or 'USD'
	amount = float(amount) if amount is not None else None
	result = Payment(Items=items, Description=description, ExpectedAmount=amount, ExpectedCurrency=currency)
	return result
