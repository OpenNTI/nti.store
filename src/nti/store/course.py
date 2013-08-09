#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
Defines course object and operations on them

$Id: purchasable.py 22284 2013-08-09 20:10:08Z carlos.sanchez $
"""
from __future__ import print_function, unicode_literals, absolute_import
__docformat__ = "restructuredtext en"

from zope import interface

from nti.ntiids import interfaces as nid_interfaces

from nti.utils.schema import AdaptingFieldProperty
from nti.utils.schema import createDirectFieldProperties

from . import purchasable
from . import interfaces as store_interfaces

@interface.implementer(store_interfaces.ICourse)
class Course(purchasable.Purchasable):
	createDirectFieldProperties(store_interfaces.ICourse)
	Description = AdaptingFieldProperty(store_interfaces.IPurchasable['Description'])

	def __repr__(self):
		return "%s(%s,%s)" % (self.__class__, self.Description, self.NTIID)

	def __eq__(self, other):
		try:
			return self is other or (store_interfaces.ICourse.providedBy(other)
									 and self.NTIID == other.NTIID)
		except AttributeError:
			return NotImplemented

def create_course(ntiid, provider=None, amount=0.0, currency='USD', items=(), fee=None, title=None, license_=None,
				  author=None, description=None, icon=None, discountable=False, bulk_purchase=False):
	amount = amount or 0.0
	if amount and not provider:
		raise AssertionError("Must specfify a provider")
	result = purchasable.create_purchasable(ntiid=ntiid, provider=provider, amount=amount, currency=currency,
											items=items, fee=fee, title=title, license_=license_, author=author,
											description=description, icon=icon, discountable=discountable,
											bulk_purchase=bulk_purchase, cls=Course)
	return result

@interface.implementer(nid_interfaces.INTIIDResolver)
class _CourseResolver(object):

	def resolve(self, ntiid_string):
		return purchasable.get_purchasable(ntiid_string)
