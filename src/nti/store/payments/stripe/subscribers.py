#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import component
from zope.annotation import IAnnotations

from .interfaces import IStripeCustomer
from .interfaces import IRegisterStripeToken
from .interfaces import IRegisterStripeCharge
from .interfaces import IStripeCustomerCreated
from .interfaces import IStripeCustomerDeleted
from .interfaces import IStripePurchaseAttempt

@component.adapter(IStripeCustomerCreated)
def stripe_customer_created(event):
	user = event.user
	su = IStripeCustomer(user, None)
	if su is not None:
		su.customer_id = event.customer_id

@component.adapter(IStripeCustomerDeleted)
def stripe_customer_deleted(event):
	user = event.user
	su = IStripeCustomer(user, None)
	if su is not None:
		su.customer_id = None
		module = "%s.%s" % (su.__class__.__module__, su.__class__.__name__)
		IAnnotations(user).pop(module, None)

@component.adapter(IRegisterStripeToken)
def register_stripe_token(event):
	purchase = event.purchase
	sp = IStripePurchaseAttempt(purchase)
	sp.TokenID = event.token
	logger.debug("Purchase %s was associated with stripe token %s",
				 purchase.id, event.token)
	
@component.adapter(IRegisterStripeCharge)
def register_stripe_charge(event):
	purchase = event.purchase
	sp = IStripePurchaseAttempt(purchase)
	sp.ChargeID = event.charge_id
	su = IStripeCustomer(purchase.creator, None)
	if su is not None:
		su.Charges.add(event.charge_id)
	logger.debug("Purchase %s was associated with stripe charge %s",
				 purchase.id, event.charge_id)
