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

from nti.schema.eqhash import EqHash

from nti.schema.field import SchemaConfigured

from nti.schema.fieldproperty import createDirectFieldProperties

from nti.store.payments.payeezy.interfaces import IPayeezyConnectKey

from nti.store.utils import MetaStoreObject

from nti.property.property import alias


@WithRepr
@EqHash('Provider',)
@interface.implementer(IPayeezyConnectKey, IContentTypeAware)
class PayeezyConnectKey(SchemaConfigured):
    createDirectFieldProperties(IPayeezyConnectKey)

    __metaclass__ = MetaStoreObject

    Alias = alias('Provider')
