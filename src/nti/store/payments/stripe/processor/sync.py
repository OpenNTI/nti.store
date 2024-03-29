#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import time
from datetime import date

from zope.event import notify

from nti.base._compat import text_

from nti.store.interfaces import PurchaseAttemptFailed
from nti.store.interfaces import PurchaseAttemptSynced
from nti.store.interfaces import PurchaseAttemptRefunded
from nti.store.interfaces import PurchaseAttemptSuccessful

from nti.store.payments.stripe.interfaces import RegisterStripeCharge
from nti.store.payments.stripe.interfaces import IStripePurchaseAttempt

from nti.store.payments.stripe.processor.base import get_api_key
from nti.store.payments.stripe.processor.base import get_charges
from nti.store.payments.stripe.processor.base import BaseProcessor

from nti.store.payments.stripe.stripe_io import get_stripe_token
from nti.store.payments.stripe.stripe_io import get_stripe_charge

from nti.store.payments.stripe.utils import create_payment_charge
from nti.store.payments.stripe.utils import adapt_to_purchase_error

from nti.store.store import get_purchase_attempt


def sync_purchase(purchase_id, username=None, api_key=None, request=None):
    """
    Attempts to synchronize a purchase attempt with the information collected in
    stripe.com and/or local db.
    """
    purchase = get_purchase_attempt(purchase_id)
    if purchase is None:
        logger.error('Purchase %r for user %s could not be found in dB',
                     purchase_id, username)
        return None

    api_key = api_key or get_api_key(purchase)
    if api_key is None:
        logger.error('Could not get a valid provider for purchase %r',
                     purchase_id)
        return None

    charge = None
    message = None
    do_synch = False
    sp = IStripePurchaseAttempt(purchase)
    if sp.ChargeID:
        charge = get_stripe_charge(sp.ChargeID, api_key=api_key)
        if charge is None:
            # if the charge cannot be found it means there was a db error
            # or the charge has been deleted from stripe.
            message = u"Charge %s cannot be found in Stripe" % sp.ChargeID
            logger.warn('Charge %s for purchase %r/%s could not be found in Stripe',
                        sp.ChargeID, purchase_id, username)
    else:
        start_time = purchase.StartTime
        start_time = time.mktime(date.fromtimestamp(start_time).timetuple())
        charges = get_charges(purchase_id=purchase_id, 
                              start_time=start_time,
                              api_key=api_key)
        if charges:
            charge = charges[0]
            notify(RegisterStripeCharge(purchase, charge.id))
        elif sp.TokenID:
            token = get_stripe_token(sp.TokenID, api_key=api_key)
            if token is None:
                # if the token cannot be found it means there was a db error
                # or the token has been deleted from stripe.
                message = u'Token %s could not found in Stripe' % sp.TokenID
                logger.warn('Token %s for purchase %r/%s could not found in Stripe',
                            sp.TokenID, purchase_id, username)
                if not purchase.has_completed():
                    do_synch = True
                    error = adapt_to_purchase_error(message)
                    notify(PurchaseAttemptFailed(purchase, error))
            elif token.used:
                tid = sp.TokenID
                message = u"Token %s has been used and no charge was found" % tid
                logger.warn(message)
                if not purchase.has_completed():
                    do_synch = True
                    error = adapt_to_purchase_error(message)
                    notify(PurchaseAttemptFailed(purchase, error))
            elif not purchase.is_pending():  # no charge and unused token
                logger.warn('No charge and unused token. Incorrect status for ' +
                            'purchase %r/%s', purchase_id, username)

    if charge:
        do_synch = True
        if charge.paid and not purchase.has_succeeded():
            pc = create_payment_charge(charge)
            notify(PurchaseAttemptSuccessful(purchase, pc, request))
        elif charge.failure_message and not purchase.has_failed():
            message = text_(charge.failure_message)
            error = adapt_to_purchase_error(message)
            notify(PurchaseAttemptFailed(purchase, error))
        elif charge.refunded and not purchase.is_refunded():
            notify(PurchaseAttemptRefunded(purchase))
    elif time.time() - purchase.StartTime >= 180 and not purchase.has_completed():
        do_synch = True
        message = message or u"Failed purchase after expiration time"
        notify(PurchaseAttemptFailed(purchase, adapt_to_purchase_error(message)))

    if do_synch:
        notify(PurchaseAttemptSynced(purchase))
    return charge


class SyncProcessor(BaseProcessor):

    @classmethod
    def sync_purchase(cls, purchase_id, username, api_key=None, request=None):
        result = sync_purchase(purchase_id=purchase_id, username=username,
                               api_key=api_key, request=request)
        return result
