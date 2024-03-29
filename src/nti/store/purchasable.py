#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Defines purchasable object and operations on them

.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import six

from zope import component
from zope import interface

from zope.location.interfaces import IContained

from zope.mimetype.interfaces import IContentTypeAware

from nti.coremetadata.interfaces import SYSTEM_USER_ID

from nti.dublincore.datastructures import PersistentCreatedModDateTrackingObject

from nti.externalization.interfaces import LocatedExternalDict
from nti.externalization.interfaces import LocatedExternalList
from nti.externalization.interfaces import StandardExternalFields
from nti.externalization.interfaces import IInternalObjectExternalizer

from nti.externalization.representation import WithRepr

from nti.property.property import alias

from nti.schema.eqhash import EqHash

from nti.schema.fieldproperty import AdaptingFieldProperty
from nti.schema.fieldproperty import createDirectFieldProperties

from nti.store.interfaces import IPurchasable
from nti.store.interfaces import IPurchasableVendorInfo
from nti.store.interfaces import IPurchasableChoiceBundle

from nti.store.model import ItemBundle

from nti.store.utils import to_frozenset
from nti.store.utils import to_collection
from nti.store.utils import MetaStoreObject

MIMETYPE = StandardExternalFields.MIMETYPE

logger = __import__('logging').getLogger(__name__)


@interface.implementer(IPurchasableVendorInfo, IInternalObjectExternalizer)
class DefaultPurchasableVendorInfo(dict):
    """
    The default representation of vendor info.
    """

    def toExternalObject(self, **unused_kwargs):
        result = LocatedExternalDict(self)
        result[MIMETYPE] = 'application/vnd.nextthought.store.purchasablevendorinfo'
        return result


@six.add_metaclass(MetaStoreObject)
@WithRepr
@EqHash('NTIID',)
@interface.implementer(IPurchasable, IContained, IContentTypeAware)
class Purchasable(PersistentCreatedModDateTrackingObject, ItemBundle):
    createDirectFieldProperties(IPurchasable)
    Description = AdaptingFieldProperty(IPurchasable['Description'])

    creator = SYSTEM_USER_ID

    IsPurchasable = True

    isPublic = alias('Public')
    isGiftable = alias('Giftable')

    __parent__ = None
    __name__ = ntiid = alias('NTIID')

    def isPublic(self):
        return self.Public
    is_public = isPublic


@interface.implementer(IPurchasableChoiceBundle)
class PurchasableChoiceBundle(Purchasable):
    __external_class_name__ = 'Purchasable'
    IsPurchasable = False


def create_purchasable(ntiid, provider, amount, currency=u'USD', items=(), fee=None,
                       title=None, license_=None, author=None, description=None,
                       icon=None, thumbnail=None, discountable=False, giftable=False,
                       redeem_cutoff_date=None, purchase_cutoff_date=None,
                       redeemable=False, bulk_purchase=True, public=True,
                       vendor_info=None, factory=Purchasable, **unused_kwargs):

    fee = float(fee) if fee is not None else None
    amount = float(amount) if amount is not None else amount
    items = to_frozenset(items) if items else frozenset((ntiid,))
    vendor = IPurchasableVendorInfo(vendor_info, None)

    result = factory(NTIID=ntiid, Provider=provider, Title=title, Author=author,
                     Items=items, Description=description, Amount=amount,
                     Currency=currency, Fee=fee, License=license_, Giftable=giftable,
                     Redeemable=redeemable, Discountable=discountable,
                     BulkPurchase=bulk_purchase, Icon=icon, Thumbnail=thumbnail,
                     Public=public, RedeemCutOffDate=redeem_cutoff_date,
                     PurchaseCutOffDate=purchase_cutoff_date, VendorInfo=vendor)
    return result


def get_purchasable(pid, registry=component):
    result = registry.queryUtility(IPurchasable, pid)
    return result


def get_purchasables(registry=component, provided=IPurchasable):
    result = LocatedExternalList()
    for _, purchasable in list(registry.getUtilitiesFor(provided)):
        result.append(purchasable)
    return result
get_all_purchasables = get_purchasables


def get_purchasable_choice_bundles(registry=component):
    return get_purchasables(registry=registry, provided=IPurchasableChoiceBundle)


def expand_purchase_item_ids(context, registry=component):
    """
    return the ids of the items that were purchased
    """
    result = set()
    context = getattr(context, 'Items', context)
    purchasables_ids = to_collection(context)
    for item in purchasables_ids:
        p = get_purchasable(item, registry=registry)
        if p is not None:
            result.update(p.Items)
    return result


def get_providers(purchasables):
    result = {p.Provider for p in purchasables or ()}
    return sorted(result)
