#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import component
from zope import interface

from nti.externalization.interfaces import IExternalObjectDecorator

from nti.externalization.singleton import Singleton

from nti.store.interfaces import IPurchaseAttempt

from nti.store.payments.payeezy import PAYEEZY

from nti.store.payments.payeezy.interfaces import IPayeezyPurchaseAttempt

logger = __import__('logging').getLogger(__name__)


@component.adapter(IPurchaseAttempt)
@interface.implementer(IExternalObjectDecorator)
class PurchaseAttemptDecorator(Singleton):

    def decorateExternalObject(self, original, external):
        if original.Processor == PAYEEZY:
            ps = IPayeezyPurchaseAttempt(original)
            external['PayeezyTokenID'] = ps.token
            external['PayeezyTokenType'] = ps.token_type
            external['PayeezyTransactionID'] = ps.transaction_id
