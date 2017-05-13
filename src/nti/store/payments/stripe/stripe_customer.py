#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Stripe customer utilities.

.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope.event import notify

from nti.dataserver.users.interfaces import IUserProfile

from nti.store import get_user

from nti.store.payments.stripe.interfaces import IStripeCustomer
from nti.store.payments.stripe.interfaces import StripeCustomerCreated
from nti.store.payments.stripe.interfaces import StripeCustomerDeleted

from nti.store.payments.stripe.stripe_io import StripeIO
from nti.store.payments.stripe.stripe_io import get_stripe_customer
from nti.store.payments.stripe.stripe_io import create_stripe_customer
from nti.store.payments.stripe.stripe_io import delete_stripe_customer
from nti.store.payments.stripe.stripe_io import update_stripe_customer


def get_customer_data(user):
    result = None
    user = get_user(user)
    if user is not None:
        profile = IUserProfile(user)
        result = {
            'email': getattr(profile, 'email', None),
            'description': getattr(profile, 'description', None)
        }
    return result


def create_customer(user, coupon=None, api_key=None):
    user = get_user(user)
    if user is not None:
        params = get_customer_data(user)
        params['coupon'] = coupon
        params['api_key'] = api_key
        customer = create_stripe_customer(**params)
        notify(StripeCustomerCreated(user, customer.id))
        return customer
    return None


def delete_customer(user, api_key=None):
    result = False
    user = get_user(user)
    if user is not None:
        adapted = IStripeCustomer(user)
        customer_id = adapted.customer_id
        if customer_id:
            result = delete_stripe_customer(customer_id=customer_id,
                                            api_key=api_key)
            notify(StripeCustomerDeleted(user, adapted.customer_id))
        return result
    return False


def update_customer(user, customer=None, coupon=None, api_key=None):
    user = get_user(user)
    if user is not None:
        params = get_customer_data(user)
        params['coupon'] = coupon
        params['api_key'] = api_key
        if customer is None:
            customer = IStripeCustomer(user).customer_id
        params['customer'] = customer
        result = update_stripe_customer(**params)
        return result
    return False


def get_customer(user, api_key=None):
    user = get_user(user)
    if user is not None:
        customer_id = IStripeCustomer(user).customer_id
        result = get_stripe_customer(customer_id, api_key=api_key)
        return result
    return None


class StripeCustomer(StripeIO):

    @classmethod
    def create_customer(cls, user, coupon=None, api_key=None):
        result = create_customer(user=user, coupon=coupon, api_key=api_key)
        return result

    @classmethod
    def delete_customer(cls, user, api_key=None):
        result = delete_customer(user=user, api_key=api_key)
        return result

    @classmethod
    def update_customer(cls, user, customer=None, coupon=None, api_key=None):
        result = update_customer(user=user, customer=customer,
                                 coupon=coupon, api_key=api_key)
        return result

    @classmethod
    def get_customer(cls, user, api_key=None):
        result = get_customer(user=user, api_key=api_key)
        return result
_StripeCustomer = StripeCustomer  # BWC
