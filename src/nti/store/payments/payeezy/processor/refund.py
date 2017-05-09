#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import time

from zope.event import notify

from nti.store import MessageFactory as _

from nti.store import ROUND_DECIMAL
from nti.store import RefundException

from nti.store.charge import PaymentCharge

from nti.store.interfaces import PurchaseAttemptRefunded

from nti.store.payments.payeezy.interfaces import SUCCESS
from nti.store.payments.payeezy.interfaces import APPROVED
from nti.store.payments.payeezy.interfaces import IPayeezyPurchaseAttempt

from nti.store.payments.payeezy.model import PayeezyRefundError

from nti.store.payments.payeezy.processor import get_payeezy
from nti.store.payments.payeezy.processor import safe_error_message
from nti.store.payments.payeezy.processor import adapt_to_purchase_error

from nti.store.store import get_purchase_attempt
from nti.store.store import get_purchase_by_code


def refund_payment(payeezy, token, amount, currency,
                   card_type, cardholder_name, card_expiry, description):
    result = payeezy.token_refund(token, amount, currency,
                                  card_type=card_type,
                                  cardholder_name=cardholder_name,
                                  card_expiry=card_expiry,
                                  description=description)
    return result


def execute_refund(api_key, token, amount, currency,
                   card_type, cardholder_name, card_expiry, description):
    logger.info('executing payeezy refund for %s', description)
    payeezy = get_payeezy(api_key)
    result = refund_payment(payeezy, token, amount, currency,
                            card_type=card_type,
                            cardholder_name=cardholder_name,
                            card_expiry=card_expiry,
                            description=description)
    if result.status_code != 201:
        msg = _('Invalid status code during refund')
        e = PayeezyRefundError(msg)
        e.message = safe_error_message(result)
        e.status = result.status_code
        raise e

    data = result.json()
    status = data.get('transaction_status') or data.get('validation_status')
    if status not in (SUCCESS, APPROVED):
        msg = _('Refund failed')
        e = PayeezyRefundError(msg)
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


def find_purchase(key, username=None):
    try:
        purchase = get_purchase_by_code(key)
    except Exception:
        purchase = get_purchase_attempt(key, username)
    return purchase


class RefundProcessor(object):

    @classmethod
    def refund_purchase(cls, purchase_id, api_key, username=None, request=None):
        purchase = find_purchase(purchase_id, username)
        if purchase is None:
            msg = _("Could not find purchase attempt")
            raise RefundException(msg, purchase_id)

        try:
            if not purchase.has_succeeded():
                msg = _("Purchase cannot be refunded")
                raise RefundException(msg, purchase_id)
        
            pricing = purchase.Pricing
            currency = pricing.Currency
            amount = pricing.TotalPurchasePrice
    
            # get priced amount in cents as expected by payeezy
            # round to two decimal places first
            cents_amount = int(round(amount * 100.0, ROUND_DECIMAL))
    
            adapted = IPayeezyPurchaseAttempt(purchase)
            token = adapted.token
            if not token:
                msg = _("Cannot find FDToken for purchase")
                raise RefundException(msg, purchase_id)
            
            execute_refund(token=token,
                           currency=currency,
                           amount=cents_amount,
                           description=purchase_id,
                           card_type=adapted.token_type,
                           card_expiry=adapted.card_expiry,
                           cardholder_name=adapted.cardholder_name,
                           api_key=api_key)

            payment_charge = PaymentCharge(Amount=float(amount),
                                           Currency=currency,
                                           Created=time.time(),
                                           Name=adapted.cardholder_name)
            notify(PurchaseAttemptRefunded(purchase, payment_charge, request))

        except RefundException:
            raise
        except Exception as e:
            logger.exception("Cannot complete refund process for '%s'",
                             purchase_id)
            error = adapt_to_purchase_error(e)
            raise error
