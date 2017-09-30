#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import


class BasePaymentProcessor(object):

    def validate_coupon(self, unused_coupon):
        return True

    def apply_coupon(self, amount, unused_coupon=None):
        return amount
_BasePaymentProcessor = BasePaymentProcessor # BWC
