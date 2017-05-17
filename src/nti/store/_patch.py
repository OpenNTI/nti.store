#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from nti.base.deprecation import moved


def _patch():
    """
    move old modules that contained persitent objects to their
    new location. DO NOT Remove
    """
    moved('nti.store.refund_error', 'nti.store.model')
    moved('nti.store.pricing_error', 'nti.store.model')
    moved('nti.store.purchase_error', 'nti.store.model')
    moved('nti.store.redemption_error', 'nti.store.model')
    # stripe
    moved('nti.store.payments.stripe.stripe_error',
          'nti.store.payments.stripe.model')
    moved('nti.store.payments.stripe.stripe_adapters',
          'nti.store.payments.stripe.adapters')

_patch()
del _patch


def patch():
    pass
