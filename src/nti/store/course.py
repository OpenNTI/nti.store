#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Defines course object and operations on them

.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import datetime
from collections import Mapping

from zope import component
from zope import interface

from nti.externalization.representation import WithRepr

from nti.schema.eqhash import EqHash

from nti.schema.fieldproperty import AdaptingFieldProperty
from nti.schema.fieldproperty import createDirectFieldProperties

from nti.store.purchasable import Purchasable
from nti.store.purchasable import get_purchasable
from nti.store.purchasable import DefaultPurchasableVendorInfo

from nti.store.interfaces import IPurchasableCourse
from nti.store.interfaces import IPurchasableCourseChoiceBundle

from nti.store.utils import to_frozenset


@WithRepr
@EqHash('NTIID',)
@interface.implementer(IPurchasableCourse)
class PurchasableCourse(Purchasable):
    createDirectFieldProperties(IPurchasableCourse)
    Description = AdaptingFieldProperty(IPurchasableCourse['Description'])


@interface.implementer(IPurchasableCourseChoiceBundle)
class PurchasableCourseChoiceBundle(PurchasableCourse):
    __external_class_name__ = 'PurchasableCourseChoiceBundle'
    IsPurchasable = False


def create_course(ntiid, name=None, provider=None, amount=None, currency=u'USD',
                  items=(), fee=None, title=None, license_=None, author=None,
                  description=None, icon=None, thumbnail=None, discountable=False,
                  bulk_purchase=False, public=True, giftable=False, redeemable=False,
                  vendor_info=None, factory=PurchasableCourse,
                  purchase_cutoff_date=None, redeem_cutoff_date=None,
                  # deprecated / legacy
                  communities=None, featured=False, preview=False,
                  department=None, signature=None, startdate=None, **kwargs):

    if amount is not None and not provider:
        raise AssertionError("Must specify a provider")

    if amount is not None and not currency:
        raise AssertionError("Must specify a currency")

    fee = float(fee) if fee is not None else None
    amount = float(amount) if amount is not None else amount
    communities = to_frozenset(communities) if items else None
    items = to_frozenset(items) if items else frozenset((ntiid,))

    def _parse_time(field):
        result = field
        if isinstance(field, (datetime.datetime, datetime.date)):
            result = field.isoformat()
        return result
    startdate = _parse_time(startdate)

    if vendor_info and isinstance(vendor_info, Mapping):
        vendor = DefaultPurchasableVendorInfo(vendor_info)
    else:
        vendor = None

    result = factory()

    # basic info
    result.Name = name
    result.NTIID = ntiid
    result.Title = title
    result.Items = items
    result.Author = author
    result.Provider = provider
    result.Description = description

    # cost
    result.Fee = fee
    result.Amount = amount
    result.Currency = currency

    # flags
    result.Public = public
    result.Giftable = giftable
    result.Redeemable = redeemable
    result.Discountable = discountable
    result.BulkPurchase = bulk_purchase

    # extras
    result.Icon = icon
    result.VendorInfo = vendor
    result.Thumbnail = thumbnail
    result.RedeemCutOffDate = redeem_cutoff_date
    result.PurchaseCutOffDate = purchase_cutoff_date

    # deprecated / legacy
    result.Preview = preview
    result.License = license_
    result.Featured = featured
    result.StartDate = startdate
    result.Signature = signature
    result.Department = department
    result.Communities = communities

    return result


def get_course(course_id, registry=component):
    result = get_purchasable(course_id, registry=registry)
    return result


import zope.deferredimport
zope.deferredimport.initialize()
zope.deferredimport.deprecated(
    "Use PurchasableCourse instead",
    Course='nti.store.course:PurchasableCourse')
