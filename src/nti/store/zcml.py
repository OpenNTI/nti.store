#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Directives to be used in ZCML: registering static keys.

.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import functools

from zope import schema
from zope import interface
from zope.configuration import fields
from zope.component.zcml import utility

from .purchasable import create_purchasable

from .interfaces import IPurchasable

class IRegisterPurchasableDirective(interface.Interface):
	"""
	The arguments needed for registering a purchasable item
	"""
	ntiid = fields.TextLine(title="Purchasable item NTIID", required=True)
	title = fields.TextLine(title="Purchasable item title", required=False)
	author = fields.TextLine(title="Purchasable item author", required=False)
	description = fields.TextLine(title="Purchasable item description", required=False,
								  description="If you do not provide, this can come "
								  "from the body text of the element. It will be "
								  "interpreted as HTML.")
	amount = schema.Float(title="Cost amount", required=True)
	currency = fields.TextLine(title="Currency amount", required=False, default='USD')
	discountable = fields.Bool(title="Discountable flag", required=False, default=False)
	bulk_purchase = fields.Bool(title="Bulk purchase flag", required=False, default=True)
	icon = fields.TextLine(title='Icon URL', required=False)
	thumbnail = fields.TextLine(title='Thumbnail URL', required=False)
	fee = schema.Float(title="Percentage fee", required=False)
	provider = fields.TextLine(title='Purchasable item provider', required=True)
	license = fields.TextLine(title='Purchasable License', required=False)
	public = fields.Bool(title="Public flag", required=False, default=True)
	items = fields.Tokens(value_type=schema.TextLine(title='The item identifier'), 
						  title="Purchasable content items", required=False)

class IRegisterCourseDirective(IRegisterPurchasableDirective):
	name = schema.TextLine(title="Course name", required=False)
	
	# overrides
	amount = schema.Float(title="Cost amount", required=False, default=0.0)
	provider = fields.TextLine(title='Course provider', required=False)

	# deprecated
	featured = schema.Bool(title="Featured flag", required=False)
	startdate = schema.TextLine(title="Start date", required=False)
	preview = fields.Bool(title='Preview item flag', required=False, default=False)
	department = fields.TextLine(title='Course department', required=False)
	signature = fields.Text(title='Course/Professor signature', required=False)
	communities = fields.Tokens(value_type=schema.TextLine(title='The community'),
								title="Course communities", required=False)
	
def registerPurchasable(_context, ntiid, provider, title, description=None, amount=None,
						currency='USD', items=None, fee=None, author=None, icon=None,
						thumbnail=None, license=None, discountable=False,
						bulk_purchase=True, public=True):
	"""
	Register a purchasable
	"""
	description = _context.info.text.strip() if description is None else description
	factory = functools.partial(create_purchasable, ntiid=ntiid, 
								provider=provider, title=title, author=author, 
								description=description, items=items, amount=amount, 
								thumbnail=thumbnail, currency=currency, icon=icon,
								fee=fee, license_=license, discountable=discountable,
								bulk_purchase=bulk_purchase, public=public)
	utility(_context, provides=IPurchasable, factory=factory, name=ntiid)
	logger.debug("Purchasable '%s' has been registered", ntiid)

