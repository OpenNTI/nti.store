#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Payeezy purchase adapters.

.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import BTrees

from zope import component
from zope import interface

from zope.annotation import factory as an_factory

from zope.container.contained import Contained

from persistent import Persistent

from nti.base._compat import text_

from nti.dataserver.interfaces import IUser

from nti.property.property import alias

from nti.store.interfaces import IPurchaseAttempt

from nti.store.payments.payeezy.interfaces import IPayeezyError
from nti.store.payments.payeezy.interfaces import IPayeezyCustomer
from nti.store.payments.payeezy.interfaces import IPayeezyException
from nti.store.payments.payeezy.interfaces import IPayeezyPurchaseError
from nti.store.payments.payeezy.interfaces import IPayeezyOperationError
from nti.store.payments.payeezy.interfaces import IPayeezyPurchaseAttempt

from nti.store.payments.payeezy.model import PayeezyPurchaseError
from nti.store.payments.payeezy.model import PayeezyOperationError


@component.adapter(IUser)
@interface.implementer(IPayeezyCustomer)
class _PayeezyCustomer(Persistent, Contained):

    family = BTrees.family64

    def __init__(self):
        self.Transactions = self.family.OO.OOTreeSet()

    def __contains__(self, txid):
        return txid in self.Transactions

    transactions = alias('Transactions')
_PayeezyCustomerFactory = an_factory(_PayeezyCustomer)


@component.adapter(IPurchaseAttempt)
@interface.implementer(IPayeezyPurchaseAttempt)
class _PayeezyPurchaseAttempt(Persistent, Contained):

    @property
    def purchase(self):
        return self.__parent__
_PayeezyPurchaseAttemptFactory = an_factory(_PayeezyPurchaseAttempt)


@component.adapter(basestring)
@interface.implementer(IPayeezyPurchaseError)
def _string_purchase_error(message):
    result = PayeezyPurchaseError(Type=u"PurchaseError")
    result.Message = text_(message or u'')
    return result


@component.adapter(IPayeezyException)
@interface.implementer(IPayeezyPurchaseError)
def payeezy_exception_adapter(error):
    result = PayeezyPurchaseError(Type=u"PurchaseError")
    args = getattr(error, 'args', ())
    message = u' '.join(map(str, args))
    result.Message = message or u'Unspecified Payeezy Purchase Exception'
    return result


def payeezy_operation_adpater(error, Type, clazz=PayeezyOperationError):
    result = clazz(Type=Type)
    args = getattr(error, 'args', ())
    result.Status = getattr(error, 'status', None)
    message = error.message or u' '.join(map(str, args))
    result.Message = message or u'Unspecified Payeezy Error'
    return result


@component.adapter(basestring)
@interface.implementer(IPayeezyOperationError)
def _string_operation_error(message):
    result = PayeezyOperationError(Type=u"OperationError")
    result.Message = text_(message or '')
    return result


@component.adapter(IPayeezyError)
@interface.implementer(IPayeezyOperationError)
def payeezy_error_adpater(error):
    return payeezy_operation_adpater(error, Type=u"PayeezyError")
