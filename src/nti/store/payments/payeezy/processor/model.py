#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from nti.store.payments.payeezy.interfaces import IPayeezyPaymentProcessor


@interface.implementer(IPayeezyPaymentProcessor)
class PayeezyPaymentProcessor(object):
    pass
