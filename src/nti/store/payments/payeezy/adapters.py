#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import BTrees

from persistent import Persistent

from zope import component
from zope import interface

from zope.annotation import factory as an_factory

from zope.container.contained import Contained

from nti.base._compat import text_

from nti.base.interfaces import IBasestring

from nti.dataserver.interfaces import IUser

from nti.externalization.representation import WithRepr

from nti.property.property import alias

from nti.schema.field import SchemaConfigured

from nti.schema.fieldproperty import createDirectFieldProperties

from nti.store import MessageFactory as _

from nti.store.interfaces import IPurchaseAttempt

from nti.store.payments.payeezy.interfaces import IPayeezyError
from nti.store.payments.payeezy.interfaces import IPayeezyCustomer
from nti.store.payments.payeezy.interfaces import IPayeezyException
from nti.store.payments.payeezy.interfaces import IPayeezyPurchaseError
from nti.store.payments.payeezy.interfaces import IPayeezyOperationError
from nti.store.payments.payeezy.interfaces import IPayeezyPurchaseAttempt

from nti.store.payments.payeezy.model import PayeezyPurchaseError
from nti.store.payments.payeezy.model import PayeezyOperationError

logger = __import__('logging').getLogger(__name__)


@component.adapter(IUser)
@interface.implementer(IPayeezyCustomer)
class _PayeezyCustomer(Persistent, Contained):

    family = BTrees.family64

    def __init__(self):
        # pylint: disable=no-member
        self.Transactions = self.family.OO.OOTreeSet()

    def __contains__(self, txid):
        return txid in self.Transactions

    transactions = alias('Transactions')
_PayeezyCustomerFactory = an_factory(_PayeezyCustomer)


@WithRepr
@component.adapter(IPurchaseAttempt)
@interface.implementer(IPayeezyPurchaseAttempt)
class _PayeezyPurchaseAttempt(SchemaConfigured, Persistent, Contained):
    createDirectFieldProperties(IPayeezyPurchaseAttempt)
    
    @property
    def purchase(self):
        return self.__parent__
_PayeezyPurchaseAttemptFactory = an_factory(_PayeezyPurchaseAttempt)


@component.adapter(basestring)
@interface.implementer(IPayeezyPurchaseError)
def _string_purchase_error(message):
    result = PayeezyPurchaseError(Type=u"PurchaseError")
    result.Message = message or u''
    return result


@component.adapter(IPayeezyException)
@interface.implementer(IPayeezyPurchaseError)
def payeezy_exception_adapter(error):
    result = PayeezyPurchaseError(Type=u"PurchaseError")
    args = getattr(error, 'args', ())
    message = u' '.join(text_(x) for x in args)
    result.Status = getattr(error, 'status', None)
    result.Message = message or _(u'Unspecified Payeezy Purchase Exception')
    return result


def payeezy_operation_adapter(error, Type, clazz=PayeezyOperationError):
    result = clazz(Type=Type)
    args = getattr(error, 'args', ())
    result.Status = getattr(error, 'status', None)
    message = getattr(error, 'message', None) or u' '.join(map(str, args))
    result.Message = message or _(u'Unspecified Payeezy Error')
    return result


@component.adapter(IBasestring)
@interface.implementer(IPayeezyOperationError)
def _string_operation_error(message):
    result = PayeezyOperationError(Type=u"OperationError")
    result.Message = message or u''
    return result


@component.adapter(IPayeezyError)
@interface.implementer(IPayeezyOperationError)
def payeezy_error_adapter(error):
    return payeezy_operation_adapter(error, Type=u"PayeezyError")
