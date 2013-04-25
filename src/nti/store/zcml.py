# -*- coding: utf-8 -*-
"""
Directives to be used in ZCML: registering static keys.

$Id$
"""
from __future__ import print_function, unicode_literals, absolute_import
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import schema
from zope import interface
from zope.configuration import fields
from zope.component.zcml import utility

from .purchasable import create_purchasable
from . import interfaces as store_interfaces

class IRegisterPurchasableDirective(interface.Interface):
	"""
	The arguments needed for registering a purchasable item
	"""
	ntiid = fields.TextLine(title="Purchasable item NTIID", required=True)
	title = fields.TextLine(title="Purchasable item title", required=False)
	author = fields.TextLine(title="Purchasable item author", required=False)
	description = fields.TextLine(title="Purchasable item description", required=False)
	amount = schema.Float(title="Cost amount", required=True)
	currency = fields.TextLine(title="Currency amount", required=False, default='USD')
	discountable = fields.Bool(title="Discountable flag", required=False, default=False)
	bulk_purchase = fields.Bool(title="Bulk purchase flag", required=False, default=True)
	icon = fields.TextLine(title='Icon URL', required=False)
	fee = schema.Float(title="Percentage fee", required=False)
	provider = fields.TextLine(title='Purchasable item provider', required=True)
	items = fields.Tokens(value_type=schema.TextLine(title='The item identifier'), title="Purchasable content items", required=False)

def registerPurchasable(_context, ntiid, provider, title, description, amount, currency=None,
						items=None, fee=None, author=None, icon=None, discountable=False, bulk_purchase=True):
	"""
	Register a purchasable
	"""
	ps = create_purchasable(ntiid=ntiid, provider=provider, title=title, author=author,
							description=description, items=items, amount=amount,
							currency=currency, icon=icon, fee=fee,
							discountable=discountable, bulk_purchase=bulk_purchase)
	utility(_context, provides=store_interfaces.IPurchasable, component=ps, name=ntiid)
	logger.debug("Purchasable '%s' has been registered", ntiid)
