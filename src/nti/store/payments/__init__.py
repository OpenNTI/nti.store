# -*- coding: utf-8 -*-
"""
Base class for payment processors.

$Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

class _BasePaymentProcessor(object):

    def validate_coupon(self, coupon):
        return True

    def apply_coupon(self, amount, coupon=None):
        return amount


