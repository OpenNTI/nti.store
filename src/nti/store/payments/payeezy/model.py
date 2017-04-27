#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from zope.mimetype.interfaces import IContentTypeAware

from nti.externalization.representation import WithRepr

from nti.schema.field import SchemaConfigured

from nti.schema.fieldproperty import createDirectFieldProperties

from nti.store.payments.payeezy.interfaces import IPayeezyConnectKey

from nti.store.utils import MetaStoreObject

from nti.property.property import alias

from nti.utils.cypher import get_plaintext


@WithRepr
@interface.implementer(IPayeezyConnectKey, IContentTypeAware)
class PayeezyConnectKey(SchemaConfigured):
    createDirectFieldProperties(IPayeezyConnectKey)

    __metaclass__ = MetaStoreObject

    Alias = alias('Provider')

    def __setattr__(self, name, value):
        if name in ("APISecret", 'ReportingToken'):
            try:
                value = get_plaintext(value)
            except Exception:
                pass
        return SchemaConfigured.__setattr__(self, name, value)
