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

from zope.schema.fieldproperty import FieldPropertyStoredThroughField as FP

from nti.externalization.representation import WithRepr

from nti.schema.eqhash import EqHash

from nti.schema.field import SchemaConfigured

from nti.schema.fieldproperty import createDirectFieldProperties

from nti.store.payments.payeezy.interfaces import IPayeezyFDToken
from nti.store.payments.payeezy.interfaces import IPayeezyConnectKey
from nti.store.payments.payeezy.interfaces import IPayeezyPurchaseError
from nti.store.payments.payeezy.interfaces import IPayeezyOperationError

from nti.store.purchase_error import PurchaseError

from nti.store.utils import MetaStoreObject

from nti.property.property import alias


@WithRepr
@EqHash('Provider',)
@interface.implementer(IPayeezyConnectKey, IContentTypeAware)
class PayeezyConnectKey(SchemaConfigured):
    createDirectFieldProperties(IPayeezyConnectKey)

    __metaclass__ = MetaStoreObject

    Alias = alias('Provider')


@WithRepr
@interface.implementer(IPayeezyFDToken, IContentTypeAware)
class PayeezyFDToken(SchemaConfigured):
    createDirectFieldProperties(IPayeezyFDToken)

    __metaclass__ = MetaStoreObject


@WithRepr
@EqHash('Type', 'Code', 'Message')
@interface.implementer(IPayeezyOperationError)
class PayeezyOperationError(SchemaConfigured):
    __metaclass__ = MetaStoreObject
    createDirectFieldProperties(IPayeezyOperationError)

    def __str__(self):
        return self.Message


@interface.implementer(IPayeezyPurchaseError)
class PayeezyPurchaseError(PurchaseError):
    Status = FP(IPayeezyPurchaseError['Status'])
    HttpStatus = alias('Status')
