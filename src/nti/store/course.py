#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Defines course object and operations on them

.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import six
import datetime
import dateutil.parser

from zope import component
from zope import interface

from nti.externalization.representation import WithRepr

from nti.ntiids import interfaces as nid_interfaces

from nti.schema.schema import EqHash
from nti.schema.fieldproperty import AdaptingFieldProperty
from nti.schema.fieldproperty import createDirectFieldProperties

from .utils import to_frozenset

from .purchasable import Purchasable
from .purchasable import get_purchasable

from .interfaces import IPurchasable

from nti.deprecated import hiding_warnings
with hiding_warnings():
	from .interfaces import ICourse


@interface.implementer(ICourse)
@WithRepr
@EqHash('NTIID',)
class Course(Purchasable):
	createDirectFieldProperties(ICourse)
	Description = AdaptingFieldProperty(IPurchasable['Description'])

def create_course(ntiid, name=None, provider=None, amount=None, currency=None,
				  items=(), fee=None, title=None, license_=None, author=None,
				  description=None, icon=None, thumbnail=None, discountable=False,
				  bulk_purchase=False, communities=(), featured=False, preview=False,
				  department=None, signature=None, startdate=None, **kwargs):

	if amount and not provider:
		raise AssertionError("Must specfify a provider")

	if amount and not currency:
		raise AssertionError("Must specfify a currency")

	fee = float(fee) if fee is not None else None
	amount = float(amount) if amount is not None else amount
	communities = to_frozenset(communities) if items else None
	items = to_frozenset(items) if items else frozenset((ntiid,))

	if isinstance(startdate, six.string_types):
		dateutil.parser.parse(startdate)
	elif isinstance(startdate, datetime.date):
		startdate = startdate.isoformat()

	result = Course(NTIID=ntiid, Name=name, Provider=provider, Title=title,
					Author=author, Items=items, Description=description, Amount=amount,
					Currency=currency, Preview=preview, Fee=fee, License=license_,
					Discountable=discountable, BulkPurchase=bulk_purchase, Icon=icon,
					Thumbnail=thumbnail, Communities=communities, Featured=featured,
					Department=department, Signature=signature, StartDate=startdate,
					**kwargs)

	return result

@interface.implementer(nid_interfaces.INTIIDResolver)
class _CourseResolver(object):

	def resolve(self, ntiid_string):
		return get_purchasable(ntiid_string)

def get_course(course_id, registry=component):
	result = get_purchasable(course_id, registry=registry)
	return result
