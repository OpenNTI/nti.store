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

from nti.property.property import alias

from nti.schema.eqhash import EqHash

from nti.schema.field import SchemaConfigured

from nti.schema.fieldproperty import createDirectFieldProperties

from nti.store.model import PurchaseError

from nti.store.payments.payeezy import PAYEEZY

from nti.store.payments.payeezy.interfaces import IPayeezyFDToken
from nti.store.payments.payeezy.interfaces import IPayeezyConnectKey
from nti.store.payments.payeezy.interfaces import IPayeezyRefundError
from nti.store.payments.payeezy.interfaces import IPayeezyPurchaseError
from nti.store.payments.payeezy.interfaces import IPayeezyOperationError

from nti.store.model import RefundError

from nti.store.utils import MetaStoreObject


@WithRepr
@EqHash('Provider',)
@interface.implementer(IPayeezyConnectKey, IContentTypeAware)
class PayeezyConnectKey(SchemaConfigured):
    __metaclass__ = MetaStoreObject
    createDirectFieldProperties(IPayeezyConnectKey)

    Processor = PAYEEZY
    Alias = name = alias('Provider')


@WithRepr
@interface.implementer(IPayeezyFDToken, IContentTypeAware)
class PayeezyFDToken(SchemaConfigured):
    __metaclass__ = MetaStoreObject
    createDirectFieldProperties(IPayeezyFDToken)


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


@interface.implementer(IPayeezyRefundError)
class PayeezyRefundError(RefundError):
    Status = FP(IPayeezyRefundError['Status'])
    HttpStatus = alias('Status')
