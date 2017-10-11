#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from nti.store.payments.payeezy import PAYEEZY

from nti.store.pricing import DefaultPurchasablePricer


class PayeezyPurchasablePricer(DefaultPurchasablePricer):
    processor = PAYEEZY
