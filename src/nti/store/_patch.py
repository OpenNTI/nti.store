#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from nti.base.deprecation import moved


def _patch():
    """
    move old modules that contained persitent objects to their
    new location. DO NOT Remove
    """
    moved('nti.store.refund_error', 'nti.store.model')
    moved('nti.store.pricing_error', 'nti.store.model')
    moved('nti.store.purchase_error', 'nti.store.model')
    moved('nti.store.purchase_index', 'nti.store.index')
    moved('nti.store.redemption_error', 'nti.store.model')


_patch()
del _patch


def patch():
    pass
