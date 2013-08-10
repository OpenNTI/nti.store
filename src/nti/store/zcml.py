#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
Directives to be used in ZCML: registering static keys.

$Id$
"""
from __future__ import print_function, unicode_literals, absolute_import
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import functools

from zope import schema
from zope import interface
from zope.configuration import fields
from zope.component.zcml import utility

from .course import create_course
from .purchasable import create_purchasable
from . import interfaces as store_interfaces

class IRegisterPurchasableDirective(interface.Interface):
	"""
	The arguments needed for registering a purchasable item
	"""
	ntiid = fields.TextLine(title="Purchasable item NTIID", required=True)
	title = fields.TextLine(title="Purchasable item title", required=False)
	author = fields.TextLine(title="Purchasable item author", required=False)
	description = fields.TextLine(title="Purchasable item description", required=False,
								  description="If you do not provide, this can come from the body text of the element. Will be interpreted as HTML.")
	amount = schema.Float(title="Cost amount", required=True)
	currency = fields.TextLine(title="Currency amount", required=False, default='USD')
	discountable = fields.Bool(title="Discountable flag", required=False, default=False)
	bulk_purchase = fields.Bool(title="Bulk purchase flag", required=False, default=True)
	icon = fields.TextLine(title='Icon URL', required=False)
	fee = schema.Float(title="Percentage fee", required=False)
	provider = fields.TextLine(title='Purchasable item provider', required=True)
	license = fields.TextLine(title='Purchasable License', required=False)
	items = fields.Tokens(value_type=schema.TextLine(title='The item identifier'), title="Purchasable content items", required=False)

class IRegisterCourseDirective(IRegisterPurchasableDirective):
	amount = schema.Float(title="Cost amount", required=False)
	currency = fields.TextLine(title="Currency amount", required=False)
	provider = fields.TextLine(title='Course provider', required=False)

def do_registration(creator_func, iface, _context, ntiid, provider, title, description=None,
					amount=None, currency=None, items=None, fee=None, author=None, icon=None,
					license_=None, discountable=False, bulk_purchase=True):

	if description is None:
		description = _context.info.text.strip()  # TODO: Will leading spaces matter across multiple lines?

	# It is important to use a factory rather than create the component because
	# the call may depend on other registrations like adapters being in effect
	factory = functools.partial(creator_func, ntiid=ntiid, provider=provider, title=title, author=author,
								description=description, items=items, amount=amount,
								currency=currency, icon=icon, fee=fee, license_=license_,
								discountable=discountable, bulk_purchase=bulk_purchase)
	utility(_context, provides=iface, factory=factory, name=ntiid)
	
def registerPurchasable(_context, ntiid, provider, title, description=None, amount=None, currency=None,
						items=None, fee=None, author=None, icon=None, license=None, discountable=False,
						bulk_purchase=True):
	"""
	Register a purchasable
	"""
	do_registration(create_purchasable, store_interfaces.IPurchasable, _context,
					ntiid=ntiid, provider=provider, title=title, description=description,
					amount=amount, currency=currency, items=items, fee=fee, author=author,
					icon=icon, license_=license, discountable=discountable, bulk_purchase=bulk_purchase)
	logger.debug("Purchasable '%s' has been registered", ntiid)


def registerCourse(_context, ntiid, title, description=None, provider=None, amount=None, currency=None,
				   items=None, fee=None, author=None, icon=None, license=None, discountable=False,
				   bulk_purchase=False):
	"""
	Register a course
	"""
	do_registration(create_course, store_interfaces.ICourse, _context,
					ntiid=ntiid, provider=provider, title=title, description=description,
					amount=amount, currency=currency, items=items, fee=fee, author=author,
					icon=icon, license_=license, discountable=discountable, bulk_purchase=bulk_purchase)
	logger.debug("Course '%s' has been registered", ntiid)
