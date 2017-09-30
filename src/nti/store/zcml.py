#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from functools import partial

from zope import schema
from zope import interface

from zope.component.zcml import utility

from zope.configuration import fields

from nti.store.interfaces import IPurchasable

from nti.store.purchasable import create_purchasable

from nti.store.schema import DateTime

logger = __import__('logging').getLogger(__name__)


class IRegisterPurchasableDirective(interface.Interface):
    """
    The arguments needed for registering a purchasable item
    """

    ntiid = fields.TextLine(title=u"Purchasable item NTIID", required=True)

    title = fields.TextLine(title=u"Purchasable item title", required=False)

    author = fields.TextLine(title=u"Purchasable item author", required=False)

    description = fields.TextLine(title=u"Purchasable item description",
                                  required=False,
                                  description=u"If you do not provide, this can come "
                                  u"from the body text of the element. It will be "
                                  u"interpreted as HTML.")

    amount = schema.Float(title=u"Cost amount", required=True)

    currency = fields.TextLine(title=u"Currency amount",
                               required=False,
                               default=u'USD')

    discountable = fields.Bool(title=u"Discountable flag",
                               required=False,
                               default=False)

    bulk_purchase = fields.Bool(title=u"Bulk purchase flag",
                                required=False,
                                default=True)

    icon = fields.TextLine(title=u'Icon URL', required=False)

    thumbnail = fields.TextLine(title=u'Thumbnail URL', required=False)

    fee = schema.Float(title=u"Percentage fee", required=False)

    provider = fields.TextLine(title=u'Purchasable item provider',
                               required=True)

    license = fields.TextLine(title=u'Purchasable License',
                              required=False)

    public = fields.Bool(title=u"Public flag",
                         required=False,
                         default=True)

    giftable = fields.Bool(title=u"Giftable flag",
                           required=False,
                           default=False)

    redeemable = fields.Bool(title=u"Redeemable flag",
                             required=False,
                             default=False)

    purchase_cutoff_date = DateTime(title=u"Purchase cutoff date",
                                    required=False,
                                    default=None)

    redeem_cutoff_date = DateTime(title=u"Redeem cutoff date",
                                  required=False,
                                  default=None)

    items = fields.Tokens(schema.TextLine(title=u'The item identifier'),
                          title=u"Items to purchase",
                          required=False)


def registerPurchasable(_context, ntiid, provider, title, description=None, amount=None,
                        currency=u'USD', items=None, fee=None, author=None, icon=None,
                        thumbnail=None, license=None, discountable=False, giftable=False,
                        purchase_cutoff_date=None, redeem_cutoff_date=None,
                        redeemable=False, bulk_purchase=True, public=True):
    """
    Register a purchasable
    """
    description = _context.info.text.strip() if description is None else description
    factory = partial(create_purchasable,
                      ntiid=ntiid,
                      provider=provider,
                      title=title,
                      author=author,
                      description=description,
                      items=items,
                      amount=amount,
                      thumbnail=thumbnail,
                      currency=currency,
                      icon=icon,
                      fee=fee,
                      public=public,
                      license_=license,
                      discountable=discountable,
                      redeem_cutoff_date=redeem_cutoff_date,
                      purchase_cutoff_date=purchase_cutoff_date,
                      bulk_purchase=bulk_purchase,
                      redeemable=redeemable,
                      giftable=giftable)
    utility(_context, provides=IPurchasable, factory=factory, name=ntiid)
    logger.debug("Purchasable '%s' has been registered", ntiid)
