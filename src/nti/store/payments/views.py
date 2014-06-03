# -*- coding: utf-8 -*-
"""
Payment pyramid views.

$Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from .stripe import views as stripe_views

# alias

StripePaymentView = stripe_views.StripePaymentView
CreateStripeTokenView = stripe_views.CreateStripeTokenView
GetStripeConnectKeyView = stripe_views.GetStripeConnectKeyView
StripeRefundPaymentView = stripe_views.StripeRefundPaymentView
GeneratePurchaseInvoiceWitStripeView = stripe_views.GeneratePurchaseInvoiceWitStripeView
PricePurchasableWithStripeCouponView = stripe_views.PricePurchasableWithStripeCouponView
