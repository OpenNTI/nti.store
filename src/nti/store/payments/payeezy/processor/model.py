#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from nti.store.payments import BasePaymentProcessor

from nti.store.payments.payeezy.processor.interfaces import IPayeezyPaymentProcessor

from nti.store.payments.payeezy.processor.purchase import PurchaseProcessor

from nti.store.payments.payeezy.processor.refund import RefundProcessor

from nti.store.payments.payeezy.processor.token import TokenProcessor


@interface.implementer(IPayeezyPaymentProcessor)
class PayeezyPaymentProcessor(BasePaymentProcessor, 
                              PurchaseProcessor,
                              RefundProcessor,
                              TokenProcessor):

    def sync_purchase(self, purchase_id, username, request=None):
        pass
