#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import six

from zope import interface

from zope.schema.fieldproperty import FieldPropertyStoredThroughField as FP

from zope.mimetype.interfaces import IContentTypeAware

from nti.externalization.representation import WithRepr

from nti.property.property import alias as _a

from nti.schema.eqhash import EqHash

from nti.schema.field import SchemaConfigured

from nti.schema.fieldproperty import createDirectFieldProperties

from nti.store.model import PurchaseError

from nti.store.payments.stripe import STRIPE

from nti.store.payments.stripe.interfaces import IStripeToken
from nti.store.payments.stripe.interfaces import IStripeConnectKey
from nti.store.payments.stripe.interfaces import IStripePurchaseError
from nti.store.payments.stripe.interfaces import IStripeOperationError

from nti.store.utils import MetaStoreObject

logger = __import__('logging').getLogger(__name__)


@six.add_metaclass(MetaStoreObject)
@WithRepr
@EqHash('Type', 'Code', 'Message')
@interface.implementer(IStripeOperationError)
class StripeOperationError(SchemaConfigured):
    createDirectFieldProperties(IStripeOperationError)

    def __str__(self):
        return self.Message


@interface.implementer(IStripePurchaseError)
class StripePurchaseError(PurchaseError):
    Param = FP(IStripePurchaseError['Param'])
    HttpStatus = FP(IStripePurchaseError['HttpStatus'])


@six.add_metaclass(MetaStoreObject)
@WithRepr
@EqHash('Alias',)
@interface.implementer(IStripeConnectKey, IContentTypeAware)
class StripeConnectKey(SchemaConfigured):
    createDirectFieldProperties(IStripeConnectKey)

    key = _a('PrivateKey')
    alias = name = Provider = _a('Alias')

    Processor = STRIPE


@six.add_metaclass(MetaStoreObject)
@WithRepr
@interface.implementer(IStripeToken, IContentTypeAware)
class StripeToken(SchemaConfigured):
    createDirectFieldProperties(IStripeToken)
    
    ID = _a('Value')
