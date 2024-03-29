#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import BTrees

from zope import component

from zope.component.hooks import getSite

from zope.catalog.interfaces import ICatalog

from zope.intid.interfaces import IIntIds

from zope.location import locate

from nti.site.interfaces import IHostPolicyFolder

from nti.store.interfaces import IPurchasable
from nti.store.interfaces import IPurchaseAttempt
from nti.store.interfaces import IRedeemedPurchaseAttempt

from nti.traversal.traversal import find_interface

from nti.zope_catalog.catalog import Catalog

from nti.zope_catalog.datetime import TimestampToNormalized64BitIntNormalizer

from nti.zope_catalog.index import NormalizationWrapper
from nti.zope_catalog.index import AttributeKeywordIndex
from nti.zope_catalog.index import SetIndex as RawSetIndex
from nti.zope_catalog.index import ValueIndex as RawValueIndex
from nti.zope_catalog.index import AttributeValueIndex as ValueIndex
from nti.zope_catalog.index import IntegerValueIndex as RawIntegerValueIndex

from nti.zope_catalog.number import FloatToNormalized64BitIntNormalizer

from nti.zope_catalog.string import StringTokenNormalizer

CATALOG_NAME = 'nti.dataserver.++etc++purchase-catalog'

IX_SITE = 'site'
IX_ITEMS = 'items'
IX_STATE = 'state'
IX_CREATOR = 'creator'
IX_MIMETYPE = 'mimeType'
IX_REV_ITEMS = 'revItems'
IX_REDEMPTION_CODE = 'redemptionCode'
IX_STARTTIME = IX_CREATEDTIME = 'startTime'

logger = __import__('logging').getLogger(__name__)


class ValidatingSiteName(object):

    __slots__ = ('site',)

    def __init__(self, obj, unused_default=None):
        if IPurchaseAttempt.providedBy(obj):
            site = getSite()
            self.site = getattr(site, '__name__', None)

    def __reduce__(self):
        raise TypeError()


class SiteIndex(ValueIndex):
    default_field_name = 'site'
    default_interface = ValidatingSiteName


class MimeTypeIndex(ValueIndex):
    default_field_name = 'mimeType'
    default_interface = IPurchaseAttempt


class RedemptionCodeIndex(ValueIndex):
    default_field_name = 'RedemptionCode'
    default_interface = IRedeemedPurchaseAttempt


class ValidatingCreator(object):

    __slots__ = ('creator',)

    def __init__(self, obj, unused_default=None):
        try:
            if IPurchaseAttempt.providedBy(obj):
                username = getattr(obj.creator, 'username', obj.creator)
                username = getattr(username, 'id', username)
                self.creator = username
        except (AttributeError, TypeError):
            pass

    def __reduce__(self):
        raise TypeError()


def CreatorIndex(family=BTrees.family64):
    return NormalizationWrapper(field_name='creator',
                                interface=ValidatingCreator,
                                index=RawValueIndex(family=family),
                                normalizer=StringTokenNormalizer())


class ItemsRawIndex(RawSetIndex):
    pass


def ItemsIndex(family=BTrees.family64):
    return NormalizationWrapper(field_name='Items',
                                interface=IPurchaseAttempt,
                                normalizer=StringTokenNormalizer(),
                                index=ItemsRawIndex(family=family),
                                is_collection=True)


class StartTimeRawIndex(RawIntegerValueIndex):
    pass


def StartTimeIndex(family=BTrees.family64):
    return NormalizationWrapper(field_name='StartTime',
                                interface=IPurchaseAttempt,
                                index=StartTimeRawIndex(family=family),
                                normalizer=TimestampToNormalized64BitIntNormalizer())


class StateRawIndex(RawValueIndex):
    pass


def StateIndex(family=BTrees.family64):
    return NormalizationWrapper(field_name='State',
                                interface=IPurchaseAttempt,
                                index=StateRawIndex(family=family),
                                normalizer=StringTokenNormalizer())


class RevItems(object):

    __slots__ = ('context',)

    def __init__(self, context, unused_default=None):
        self.context = context

    @property
    def items(self):
        if IPurchaseAttempt.providedBy(self.context):
            result = self.context.Items
            return result


def RevItemsIndex(family=BTrees.family64):
    return AttributeKeywordIndex(field_name='items',
                                 interface=RevItems,
                                 family=family)


class StoreCatalog(Catalog):
    pass


def get_purchase_catalog(registry=component):
    return registry.queryUtility(ICatalog, name=CATALOG_NAME)


def create_purchase_catalog(catalog=None, family=BTrees.family64):
    if catalog is None:
        catalog = StoreCatalog(family=family)
    for name, clazz in ((IX_SITE, SiteIndex),
                        (IX_ITEMS, ItemsIndex),
                        (IX_STATE, StateIndex),
                        (IX_CREATOR, CreatorIndex),
                        (IX_MIMETYPE, MimeTypeIndex),
                        (IX_REV_ITEMS, RevItemsIndex),
                        (IX_CREATEDTIME, StartTimeIndex),
                        (IX_REDEMPTION_CODE, RedemptionCodeIndex)):
        index = clazz(family=family)
        locate(index, catalog, name)
        catalog[name] = index
    return catalog


def install_purchase_catalog(site_manager_container, intids=None):
    lsm = site_manager_container.getSiteManager()
    intids = intids if intids is not None else lsm.getUtility(IIntIds)
    catalog = get_purchase_catalog(lsm)
    if catalog is not None:
        return catalog

    catalog = create_purchase_catalog(family=intids.family)
    locate(catalog, site_manager_container, CATALOG_NAME)
    intids.register(catalog)
    lsm.registerUtility(catalog, 
                        provided=ICatalog, 
                        name=CATALOG_NAME)
    for index in catalog.values():
        intids.register(index)
    return catalog


# purchasable index


PURCHASABLE_CATALOG_NAME = 'nti.dataserver.++etc++purchasable-catalog'

IX_LABEL = 'label'
IX_NTIID = 'ntiid'
IX_PUBLIC = 'public'
IX_AMOUNT = 'Amount'
IX_CURRENCY = 'currency'
IX_PROVIDER = 'provider'


class ValidatingPurchasableSiteName(object):

    __slots__ = ('site',)

    def __init__(self, obj, unused_default=None):
        if IPurchasable.providedBy(obj):
            folder = find_interface(obj, IHostPolicyFolder, strict=False)
            self.site = getattr(folder, '__name__', None)

    def __reduce__(self):
        raise TypeError()


class PurchasableSiteIndex(ValueIndex):
    default_field_name = 'site'
    default_interface = ValidatingPurchasableSiteName
    

class PurchasableItemsRawIndex(RawSetIndex):
    pass


def PurchasableItemsIndex(family=BTrees.family64):
    return NormalizationWrapper(field_name='Items',
                                interface=IPurchasable,
                                normalizer=StringTokenNormalizer(),
                                index=PurchasableItemsRawIndex(family=family),
                                is_collection=True)


class PurchasableRevItems(object):

    __slots__ = ('context',)

    def __init__(self, context, unused_default=None):
        self.context = context

    @property
    def items(self):
        if IPurchasable.providedBy(self.context):
            result = self.context.Items
            return result


def PurchasableRevItemsIndex(family=BTrees.family64):
    return AttributeKeywordIndex(field_name='items',
                                 interface=PurchasableRevItems,
                                 family=family)


class PurchasableMimeTypeIndex(ValueIndex):
    default_field_name = 'mimeType'
    default_interface = IPurchasable


class PurchasableNTIIDIndex(ValueIndex):
    default_field_name = 'NTIID'
    default_interface = IPurchasable


class PurchasableLabelIndex(ValueIndex):
    default_field_name = 'Label'
    default_interface = IPurchasable


class PurchasableProviderIndex(ValueIndex):
    default_field_name = 'Provider'
    default_interface = IPurchasable
    

class PurchasablePublicIndex(ValueIndex):
    default_field_name = 'Public'
    default_interface = IPurchasable


class PurchasableAmountRawIndex(RawIntegerValueIndex):
    pass


def PurchasableAmountIndex(family=BTrees.family64):
    return NormalizationWrapper(field_name='Amount',
                                interface=IPurchasable,
                                index=PurchasableAmountRawIndex(family=family),
                                normalizer=FloatToNormalized64BitIntNormalizer())


class PurchasableCurrencyIndex(ValueIndex):
    default_field_name = 'Currency'
    default_interface = IPurchasable


class PurchasableCatalog(Catalog):
    pass


def get_purchasable_catalog(registry=component):
    catalog = registry.queryUtility(ICatalog, name=PURCHASABLE_CATALOG_NAME)
    return catalog


def create_purchasable_catalog(catalog=None, family=BTrees.family64):
    if catalog is None:
        catalog = PurchasableCatalog(family=family)
    for name, clazz in ((IX_SITE, PurchasableSiteIndex),
                        (IX_LABEL, PurchasableLabelIndex),
                        (IX_NTIID, PurchasableNTIIDIndex),
                        (IX_ITEMS, PurchasableItemsIndex),
                        (IX_AMOUNT, PurchasableAmountIndex),
                        (IX_PUBLIC, PurchasablePublicIndex),
                        (IX_CURRENCY, PurchasableCurrencyIndex),
                        (IX_PROVIDER, PurchasableProviderIndex),
                        (IX_MIMETYPE, PurchasableMimeTypeIndex),
                        (IX_REV_ITEMS, PurchasableRevItemsIndex)):
        index = clazz(family=family)
        locate(index, catalog, name)
        catalog[name] = index
    return catalog


def install_purchasable_catalog(site_manager_container, intids=None):
    lsm = site_manager_container.getSiteManager()
    intids = intids if intids is not None else lsm.getUtility(IIntIds)
    catalog = get_purchasable_catalog(lsm)
    if catalog is not None:
        return catalog

    catalog = create_purchasable_catalog(family=intids.family)
    locate(catalog, site_manager_container, PURCHASABLE_CATALOG_NAME)
    intids.register(catalog)
    lsm.registerUtility(catalog, 
                        provided=ICatalog, 
                        name=PURCHASABLE_CATALOG_NAME)
    for index in catalog.values():
        intids.register(index)
    return catalog
