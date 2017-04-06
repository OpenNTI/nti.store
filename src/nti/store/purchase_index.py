#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope.component.hooks import getSite

from zope.catalog.interfaces import ICatalog

from zope.intid.interfaces import IIntIds

from zope.location import locate

from nti.base._compat import unicode_

from nti.store import CATALOG_NAME

from nti.store.interfaces import IPurchaseAttempt
from nti.store.interfaces import IRedeemedPurchaseAttempt

from nti.zope_catalog.catalog import Catalog

from nti.zope_catalog.datetime import TimestampToNormalized64BitIntNormalizer

from nti.zope_catalog.index import NormalizationWrapper
from nti.zope_catalog.index import AttributeKeywordIndex
from nti.zope_catalog.index import SetIndex as RawSetIndex
from nti.zope_catalog.index import ValueIndex as RawValueIndex
from nti.zope_catalog.index import AttributeValueIndex as ValueIndex
from nti.zope_catalog.index import IntegerValueIndex as RawIntegerValueIndex

from nti.zope_catalog.string import StringTokenNormalizer

IX_SITE = 'site'
IX_ITEMS = 'items'
IX_STATE = 'state'
IX_CREATOR = 'creator'
IX_MIMETYPE = 'mimeType'
IX_REV_ITEMS = 'revItems'
IX_REDEMPTION_CODE = 'redemptionCode'
IX_STARTTIME = IX_CREATEDTIME = 'startTime'


class ValidatingSiteName(object):

    __slots__ = (b'site',)

    def __init__(self, obj, default=None):
        if IPurchaseAttempt.providedBy(obj):
            self.site = unicode_(getSite().__name__)

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

    __slots__ = (b'creator',)

    def __init__(self, obj, default=None):
        try:
            if IPurchaseAttempt.providedBy(obj):
                username = getattr(obj.creator, 'username', obj.creator)
                username = getattr(username, 'id', username)
                self.creator = username
        except (AttributeError, TypeError):
            pass

    def __reduce__(self):
        raise TypeError()


def CreatorIndex(family=None):
    return NormalizationWrapper(field_name='creator',
                                interface=ValidatingCreator,
                                index=RawValueIndex(family=family),
                                normalizer=StringTokenNormalizer())


class ItemsRawIndex(RawSetIndex):
    pass


def ItemsIndex(family=None):
    return NormalizationWrapper(field_name='Items',
                                interface=IPurchaseAttempt,
                                normalizer=StringTokenNormalizer(),
                                index=ItemsRawIndex(family=family),
                                is_collection=True)


class StartTimeRawIndex(RawIntegerValueIndex):
    pass


def StartTimeIndex(family=None):
    return NormalizationWrapper(field_name='StartTime',
                                interface=IPurchaseAttempt,
                                index=StartTimeRawIndex(family=family),
                                normalizer=TimestampToNormalized64BitIntNormalizer())


class StateRawIndex(RawValueIndex):
    pass


def StateIndex(family=None):
    return NormalizationWrapper(field_name='State',
                                interface=IPurchaseAttempt,
                                index=StateRawIndex(family=family),
                                normalizer=StringTokenNormalizer())


class RevItems(object):

    __slots__ = (b'context',)

    def __init__(self, context, default=None):
        self.context = context

    @property
    def items(self):
        if IPurchaseAttempt.providedBy(self.context):
            result = self.context.Items
            return result


def RevItemsIndex(family=None):
    return AttributeKeywordIndex(field_name='items',
                                 interface=RevItems,
                                 family=family)


class StoreCatalog(Catalog):
    pass


def install_purchase_catalog(site_manager_container, intids=None):
    lsm = site_manager_container.getSiteManager()
    intids = intids if intids is not None else lsm.getUtility(IIntIds)
    catalog = lsm.queryUtility(ICatalog, name=CATALOG_NAME)
    if catalog is not None:
        return catalog

    catalog = StoreCatalog(family=intids.family)
    catalog.__name__ = CATALOG_NAME
    catalog.__parent__ = site_manager_container
    intids.register(catalog)
    lsm.registerUtility(catalog, provided=ICatalog, name=CATALOG_NAME)

    for name, clazz in ((IX_SITE, SiteIndex),
                        (IX_ITEMS, ItemsIndex),
                        (IX_STATE, StateIndex),
                        (IX_CREATOR, CreatorIndex),
                        (IX_MIMETYPE, MimeTypeIndex),
                        (IX_REV_ITEMS, RevItemsIndex),
                        (IX_CREATEDTIME, StartTimeIndex),
                        (IX_REDEMPTION_CODE, RedemptionCodeIndex)):
        index = clazz(family=intids.family)
        intids.register(index)
        locate(index, catalog, name)
        catalog[name] = index
    return catalog
