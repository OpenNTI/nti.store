#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import six
import sys
import math
from functools import partial

from stripe.error import InvalidRequestError

from zope import component

from zope.event import notify

from nti.dataserver.interfaces import IDataserverTransactionRunner

from nti.store import MessageFactory as _

from nti.store import get_user
from nti.store import ROUND_DECIMAL
from nti.store import PurchaseException

from nti.store.interfaces import PurchaseAttemptFailed
from nti.store.interfaces import PurchaseAttemptStarted
from nti.store.interfaces import PurchaseAttemptSuccessful

from nti.store.payments.stripe.interfaces import IStripeCustomer
from nti.store.payments.stripe.interfaces import RegisterStripeToken
from nti.store.payments.stripe.interfaces import RegisterStripeCharge
from nti.store.payments.stripe.interfaces import IStripePurchaseAttempt

from nti.store.payments.stripe.processor.coupon import CouponProcessor

from nti.store.payments.stripe.processor.pricing import price_order
from nti.store.payments.stripe.processor.pricing import PricingProcessor

from nti.store.payments.stripe.stripe_customer import StripeCustomer
from nti.store.payments.stripe.stripe_customer import create_customer

from nti.store.payments.stripe.stripe_io import create_charge
from nti.store.payments.stripe.stripe_io import update_charge

from nti.store.payments.stripe.utils import get_charge_metata
from nti.store.payments.stripe.utils import create_payment_charge
from nti.store.payments.stripe.utils import adapt_to_purchase_error

from nti.store.store import get_purchase_attempt
from nti.store.store import get_purchase_purchasables


def get_transaction_runner():
    result = component.getUtility(IDataserverTransactionRunner)
    return result


def _start_purchase(purchase_id, token, username=None):
    purchase = get_purchase_attempt(purchase_id, username)
    if purchase is None:
        msg = "Could not find purchase attempt %s" % purchase_id
        raise PurchaseException(msg)

    if not purchase.is_pending():
        notify(PurchaseAttemptStarted(purchase))
        notify(RegisterStripeToken(purchase, token))

    customer_id = None
    if username:
        user = get_user(username)
        adapted = IStripeCustomer(user, None)
        customer_id = adapted.CustomerID if adapted is not None else None

    context = purchase.Context
    order = purchase.Order.copy()  # make a copy of the order
    purchasables = get_purchase_purchasables(purchase)
    description = purchase.Description \
              or (purchasables[0].Title if purchasables else None)
    metadata = get_charge_metata(purchase_id, username=username,
                                 context=context, customer_id=customer_id)
    return (order, metadata, description, customer_id)


def _execute_stripe_charge(purchase_id, cents_amount, currency, card,
                           application_fee=None, customer_id=None,
                           metadata=None, description=None, api_key=None):
    logger.info('Creating stripe charge for %s (metadata=%s)',
                purchase_id, metadata)
    metadata = metadata or {}
    description = description or None
    charge = create_charge(cents_amount, currency=currency,
                           card=card, metadata=metadata,
                           customer_id=customer_id,
                           application_fee=application_fee,
                           api_key=api_key,
                           description=description)
    return charge


def _register_charge_notify(purchase_id, charge, username=None,
                            pricing=None, request=None, api_key=None):
    purchase = get_purchase_attempt(purchase_id, username)
    if not purchase.is_pending():
        return False

    # register the charge id w/ the purchase and creator
    notify(RegisterStripeCharge(purchase, charge.id))

    # check charge
    if charge.paid:
        result = True
        purchase.Pricing = pricing
        payment_charge = create_payment_charge(charge)
        notify(PurchaseAttemptSuccessful(purchase, payment_charge, request))
    else:
        result = False
        message = charge.failure_message
        notify(PurchaseAttemptFailed(purchase, adapt_to_purchase_error(message)))
    return result


def _fail_purchase(purchase_id, error, username=None):
    purchase = get_purchase_attempt(purchase_id, username)
    if purchase is not None:
        notify(PurchaseAttemptFailed(purchase, error))


def _get_purchase(purchase_id, username=None):
    purchase = get_purchase_attempt(purchase_id, username)
    return purchase


class PurchaseProcessor(StripeCustomer, CouponProcessor, PricingProcessor):

    def _create_customer(self, transaction_runner, user, api_key=None):
        try:
            creator_func = partial(create_customer, user=user, api_key=api_key)
            result = transaction_runner(creator_func)
            if result is not None:
                logger.info("Stripe customer %s created for user %s",
                            result.id, user)
            return result
        except Exception as e:
            logger.error("Could not create stripe customer %s. %s", user, e)
        return None

    def _update_charge(self, charge, customer_id, metadata=None,
                       description=None, api_key=None):
        try:
            metadata = metadata or {}
            metadata['CustomerID'] = customer_id
            update_charge(charge,
                          metadata=metadata,
                          description=description,
                          api_key=api_key)
            logger.info("Charge %s updated", charge.id)
        except Exception as e:
            logger.error("Could not update stripe charge %s. %s", charge.id, e)
        return None

    def _update_customer(self, transaction_runner, username, customer, coupon, api_key=None):
        updater_func = partial(self.update_customer, user=username, customer=customer,
                               coupon=coupon, api_key=api_key)
        try:
            result = transaction_runner(updater_func)
            logger.info("Customer %s/%s updated", customer, username)
            return result
        except Exception:
            logger.exception("Exception while updating the user coupon.")

    def _post_purchase(self, transaction_runner, purchase_id, charge,
                       metadata=None, customer_id=None, username=None,
                       description=None, api_key=None):
        if not username:
            return

        if not customer_id:
            customer = self._create_customer(transaction_runner,
                                             username,
                                             api_key=api_key)
            customer_id = customer.id if customer is not None else None
            if customer_id:
                self._update_charge(charge=charge,
                                    api_key=api_key,
                                    metadata=metadata,
                                    customer_id=customer_id,
                                    description=description)

        getter_func = partial(_get_purchase,
                              purchase_id=purchase_id,
                              username=username)
        purchase = transaction_runner(getter_func)
        if customer_id and purchase is not None:
            # update coupon. In case there is an error updating the coupon
            # (e.g. max redemptions reached) Log error and this must be check manually
            coupon = purchase.Order.Coupon
            if coupon is not None:
                self._update_customer(transaction_runner, username=username,
                                      customer=customer_id, coupon=coupon,
                                      api_key=api_key)

    def process_purchase(self, purchase_id, token, username=None, expected_amount=None,
                         api_key=None, request=None, site_name=None):
        """
        Executes the process purchase.
        This function may be called in a greenlet
        (which cannot be run within a transaction runner);
        the request should be established when it is called.
        """
        charge = None
        success = False

        # prepare transaction runner
        transaction_runner = get_transaction_runner()
        transaction_runner = partial(transaction_runner,
                                     site_names=(site_name,) if site_name else ())

        start_purchase = partial(_start_purchase,
                                 purchase_id=purchase_id,
                                 username=username,
                                 token=token)
        try:
            # start the purchase.
            # We notify purchase has started and
            # return the order to price, charge metatada, description,
            # stripe customer id
            data = transaction_runner(start_purchase)
            order, metadata, description, customer_id = data

            # price the purchasable order
            pricer = partial(price_order, order)
            pricing = transaction_runner(pricer)

            # check priced amount w/ expected amount
            currency = pricing.Currency
            amount = pricing.TotalPurchasePrice
            if pricing.TotalPurchaseFee:
                application_fee = pricing.TotalPurchaseFee
            else:
                application_fee = None

            if      expected_amount is not None and \
                not math.fabs(expected_amount - amount) <= 0.05:
                logger.error("Purchase order amount %.2f did not match the " +
                             "expected amount %.2f", amount, expected_amount)
                raise PurchaseException("Purchase order amount did not match the "
                                        "expected amount")

            # get priced amount in cents as expected by stripe
            # round to two decimal places first
            cents_amount = int(round(amount * 100.0, ROUND_DECIMAL))
            if application_fee:
                application_fee = int(round(application_fee * 100.0, ROUND_DECIMAL))
            else:
                application_fee = None

            # execute stripe charge outside a DS transaction
            charge = _execute_stripe_charge(card=token,
                                            currency=currency,
                                            metadata=metadata,
                                            description=description,
                                            customer_id=customer_id,
                                            purchase_id=purchase_id,
                                            cents_amount=cents_amount,
                                            application_fee=application_fee,
                                            api_key=api_key)

            if charge is not None:
                register_charge_notify = partial(_register_charge_notify,
                                                 purchase_id=purchase_id,
                                                 username=username,
                                                 charge=charge,
                                                 pricing=pricing,
                                                 request=request,
                                                 api_key=api_key)
                success = transaction_runner(register_charge_notify)

            else:
                error = _("Could not execute purchase charge at Stripe")
                error = adapt_to_purchase_error(error)
                fail_purchase = partial(_fail_purchase,
                                        purchase_id=purchase_id,
                                        username=username,
                                        error=error)
                transaction_runner(fail_purchase)
        except Exception as e:
            logger.exception("Cannot complete process purchase for '%s'",
                             purchase_id)

            t, v, tb = sys.exc_info()
            error = adapt_to_purchase_error(e)
            fail_purchase = partial(_fail_purchase,
                                    purchase_id=purchase_id,
                                    username=username,
                                    error=error)
            transaction_runner(fail_purchase)

            # report exception
            raise t, v, tb

        # now we can do post purchase registration that is
        # independent of the purchase
        if success:
            self._post_purchase(transaction_runner,
                                charge=charge,
                                api_key=api_key,
                                metadata=metadata,
                                username=username,
                                description=description,
                                purchase_id=purchase_id,
                                customer_id=customer_id)

        # return charge id
        return charge.id if charge is not None else None

    def get_payment_charge(self, purchase, username=None, api_key=None):
        purchase_id = purchase  # save original
        if isinstance(purchase, six.string_types):
            purchase = get_purchase_attempt(purchase, username)

        if purchase is None:
            msg = "Could not find purchase attempt %s" % purchase_id
            raise PurchaseException(msg)

        api_key = api_key or self.get_api_key(purchase)
        if not api_key:
            msg = "Could not find a stripe key for %s" % purchase_id
            raise PurchaseException(msg)

        spurchase = IStripePurchaseAttempt(purchase)
        charge_id = spurchase.ChargeID
        try:
            if charge_id:
                charge = self.get_stripe_charge(charge_id, api_key=api_key)
            else:
                charge = None
            result = create_payment_charge(charge) if charge else None
        except InvalidRequestError:
            result = None
        return result
