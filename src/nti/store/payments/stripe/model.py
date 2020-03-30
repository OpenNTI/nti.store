#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import urllib

from persistent import Persistent
from persistent.mapping import PersistentMapping

import six

from zope import interface
from zope import lifecycleevent
from zope.container.contained import Contained

from zope.schema.fieldproperty import FieldPropertyStoredThroughField as FP

from zope.mimetype.interfaces import IContentTypeAware

from nti.base.mixins import CreatedTimeMixin

from nti.externalization.representation import WithRepr

from nti.property.property import alias as _a

from nti.schema.eqhash import EqHash

from nti.schema.fieldproperty import createDirectFieldProperties

from nti.schema.schema import SchemaConfigured

from nti.store.model import PurchaseError

from nti.store.payments.stripe import STRIPE

from nti.store.payments.stripe.interfaces import IStripeToken
from nti.store.payments.stripe.interfaces import IStripeConnectKey
from nti.store.payments.stripe.interfaces import IStripePurchaseError
from nti.store.payments.stripe.interfaces import IStripeOperationError
from nti.store.payments.stripe.interfaces import IStripeConnectKeyContainer
from nti.store.payments.stripe.interfaces import IPersistentStripeConnectKey
from nti.store.payments.stripe.interfaces import IStripeConnectConfig

from nti.store.utils import MetaStoreObject

logger = __import__('logging').getLogger(__name__)


@six.add_metaclass(MetaStoreObject)
@WithRepr
@EqHash('Type', 'Code', 'Message')
@interface.implementer(IStripeOperationError)
class StripeOperationError(SchemaConfigured):
    createDirectFieldProperties(IStripeOperationError)

    def __str__(self):
        # pylint: disable=no-member
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
@interface.implementer(IPersistentStripeConnectKey)
class PersistentStripeConnectKey(CreatedTimeMixin, StripeConnectKey, Persistent):
    createDirectFieldProperties(IPersistentStripeConnectKey)


@six.add_metaclass(MetaStoreObject)
@WithRepr
@interface.implementer(IStripeToken, IContentTypeAware)
class StripeToken(SchemaConfigured):
    createDirectFieldProperties(IStripeToken)
    
    ID = _a('Value')


@interface.implementer(IStripeConnectKeyContainer)
class StripeConnectKeyContainer(PersistentMapping, Contained):

    def add_key(self, key):
        self[key.Alias] = key
        lifecycleevent.added(key, self, key.Alias)

    def remove_key(self, key):
        name = getattr(key, 'Alias', key)
        obj = self[name]
        del self[name]
        lifecycleevent.removed(obj, self, name)


@interface.implementer(IStripeConnectConfig)
class StripeConnectConfig(SchemaConfigured):
    createDirectFieldProperties(IStripeConnectConfig)

    @property
    def StripeOauthEndpoint(self):
        params = {
            "response_type": "code",
            "scope": "read_write",
            "stripe_landing": "login",
            "client_id": self.ClientId
        }
        return self.StripeOauthBase + '?' + urllib.urlencode(params)