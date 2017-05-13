#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)


def _patch():
    try:
        from nti.common.deprecated import moved
        moved('nti.store.refund_error', 'nti.store.model')
        moved('nti.store.pricing_error', 'nti.store.model')
        moved('nti.store.purchase_error', 'nti.store.model')
        moved('nti.store.redemption_error', 'nti.store.model')
    except ImportError:
        pass


_patch()
del _patch


def patch():
    pass
