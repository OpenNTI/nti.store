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


def safe_error_message(result):
    try:
        data = result.json()
        return data['message']
    except Exception:
        return None


@interface.implementer(IPayeezyPaymentProcessor)
class PayeezyPaymentProcessor(BasePaymentProcessor):

    def sync_purchase(self, purchase_id, username):
        pass
