#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import sys
import math
import time
from functools import partial

from zope import component

from zope.event import notify

from nti.site.interfaces import ISiteTransactionRunner

from nti.store import MessageFactory as _

from nti.store import get_user
from nti.store import ROUND_DECIMAL
from nti.store import PurchaseException

from nti.store.charge import PaymentCharge

from nti.store.interfaces import PurchaseAttemptFailed
from nti.store.interfaces import PurchaseAttemptStarted
from nti.store.interfaces import PurchaseAttemptSuccessful

from nti.store.payments.payeezy.interfaces import SUCCESS
from nti.store.payments.payeezy.interfaces import APPROVED
from nti.store.payments.payeezy.interfaces import IPayeezyCustomer
from nti.store.payments.payeezy.interfaces import IPayeezyPurchaseAttempt

from nti.store.payments.payeezy.model import PayeezyPurchaseError

from nti.store.payments.payeezy.processor import get_payeezy
from nti.store.payments.payeezy.processor import safe_error_message
from nti.store.payments.payeezy.processor import adapt_to_purchase_error

from nti.store.payments.payeezy.processor.pricing import price_order
from nti.store.payments.payeezy.processor.pricing import PricingProcessor

from nti.store.store import get_purchase_attempt


def get_transaction_runner():
    return component.getUtility(ISiteTransactionRunner)


def start_purchase(purchase_id, token, token_type, card_expiry, 
                   cardholder_name, username=None):
    purchase = get_purchase_attempt(purchase_id, username)
    if purchase is None:
        msg = _("Could not find purchase attempt")
        raise PurchaseException(msg, purchase_id)

    if not purchase.is_pending():
        notify(PurchaseAttemptStarted(purchase))

    # save data
    adapted = IPayeezyPurchaseAttempt(purchase)
    adapted.token = token
    adapted.token_type = token_type
    adapted.card_expiry = card_expiry
    adapted.cardholder_name = cardholder_name
    
    # return a copy of the order
    result = purchase.Order.copy()
    return result


def fail_purchase(purchase_id, error, username=None):
    purchase = get_purchase_attempt(purchase_id, username)
    if purchase is not None:
        notify(PurchaseAttemptFailed(purchase, error))


def token_payment(payeezy, token, amount, currency,
                  card_type, cardholder_name, card_expiry, description):
    result = payeezy.token_payment(token, amount, currency,
                                   card_type=card_type,
                                   cardholder_name=cardholder_name,
                                   card_expiry=card_expiry,
                                   description=description)
    return result


def execute_charge(api_key, token, amount, currency,
                   card_type, cardholder_name, card_expiry, description):
    logger.info('executing payeezy charge for %s', description)
    payeezy = get_payeezy(api_key)
    result = token_payment(payeezy, token, amount, currency,
                           card_type=card_type,
                           cardholder_name=cardholder_name,
                           card_expiry=card_expiry,
                           description=description)
    if result.status_code != 201:
        msg = _('Invalid status code during purchase')
        e = PayeezyPurchaseError(msg)
        e.message = safe_error_message(result)
        e.status = result.status_code
        raise e

    data = result.json()
    status = data.get('transaction_status') or data.get('validation_status')
    if status not in (SUCCESS, APPROVED):
        msg = _('Purchase failed')
        e = PayeezyPurchaseError(msg)
        e.status = status
        error_messages = []
        if 'Error' in data:
            for m in data.get('messages') or ():
                error_messages.append(m.get('description') or u'')
        else:
            error_messages.append(data.get('bank_message') or u'')
            error_messages.append(data.get('gateway_message') or u'')
        e.message = u'. '.join(error_messages) or None
        raise e
    return data


def register_charge_notify(charge, purchase_id, username=None,
                           pricing=None, request=None):
    purchase = get_purchase_attempt(purchase_id, username)
    if not purchase.is_pending():
        return None

    # update purchase
    transaction_id = charge.get('transaction_id')
    payeezy_purchase = IPayeezyPurchaseAttempt(purchase)
    payeezy_purchase.transaction_id = transaction_id
    payeezy_purchase.correlation_id = charge.get('correlation_id')
    payeezy_purchase.transaction_tag = charge.get('transaction_tag')

    # crate payment charge
    purchase.Pricing = pricing
    token = charge.get('token') or {}
    token = token.get('token_data') or {}
    payment_charge = PaymentCharge(Amount=float(charge.get('amount')),
                                   Currency=charge.get('currency'),
                                   Created=time.time(),
                                   Name=token.get('cardholder_name'))
    notify(PurchaseAttemptSuccessful(purchase, payment_charge, request))

    # update user transactions
    customer = IPayeezyCustomer(get_user(username or ''), None)
    if transaction_id:
        customer.Transactions.add(transaction_id)
    return transaction_id


class PurchaseProcessor(PricingProcessor):

    @classmethod
    def process_purchase(cls, purchase_id, token,
                         card_type, cardholder_name, card_expiry,
                         api_key, username=None, expected_amount=None, request=None):

        transaction_runner = get_transaction_runner()

        starter = partial(start_purchase,
                          token=token,
                          username=username,
                          token_type=card_type,
                          card_expiry=card_expiry,
                          purchase_id=purchase_id,
                          cardholder_name=cardholder_name)
        try:
            # start the purchase.
            # We notify purchase has started and
            # return the order to price
            order = transaction_runner(starter)

            # price the purchasable order
            pricer = partial(price_order, order)
            pricing = transaction_runner(pricer)

            # check priced amount w/ expected amount
            currency = pricing.Currency
            amount = pricing.TotalPurchasePrice
            if      expected_amount is not None and \
                not math.fabs(expected_amount - amount) <= 0.05:
                logger.error("Purchase order amount %.2f did not match the " +
                             "expected amount %.2f", amount, expected_amount)
                msg = _("Purchase order amount did not match the expected amount")
                raise PurchaseException(msg)

            # get priced amount in cents as expected by payeezy
            # round to two decimal places first
            cents_amount = int(round(amount * 100.0, ROUND_DECIMAL))

            # execute payeezy charge outside a DS transaction
            charge = execute_charge(token=token,
                                    api_key=api_key,
                                    currency=currency,
                                    amount=cents_amount,
                                    card_type=card_type,
                                    card_expiry=card_expiry,
                                    description=purchase_id,
                                    cardholder_name=cardholder_name)

            register_and_notifier = partial(register_charge_notify,
                                            purchase_id=purchase_id,
                                            username=username,
                                            charge=charge,
                                            pricing=pricing,
                                            request=request)
            return transaction_runner(register_and_notifier)

        except Exception as e:
            logger.exception("Cannot complete process purchase for '%s'",
                             purchase_id)

            t, v, tb = sys.exc_info()
            error = adapt_to_purchase_error(e)
            fail_purchase = partial(fail_purchase,
                                    error=error,
                                    username=username,
                                    purchase_id=purchase_id)
            transaction_runner(fail_purchase)

            raise t, v, tb
