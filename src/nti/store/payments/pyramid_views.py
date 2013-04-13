# -*- coding: utf-8 -*-
"""
Payment pyramid views.

$Id$
"""
from __future__ import print_function, unicode_literals, absolute_import
__docformat__ = "restructuredtext en"

from .stripe import pyramid_views as stripe_pyramid

StripePaymentView = stripe_pyramid.StripePaymentView
GetStripeConnectKeyView = stripe_pyramid.GetStripeConnectKeyView
ValidateStripeCouponView = stripe_pyramid.ValidateStripeCouponView
