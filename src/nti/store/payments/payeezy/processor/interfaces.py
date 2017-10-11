#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Payeezy Payment Processor interfaces

.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from nti.store.interfaces import IPaymentProcessor


class IPayeezyPaymentProcessor(IPaymentProcessor):

    def price_purchase(purchase_id, username):
        """
        price a purchase
        """

    def refund_purchase(purchase_id, username, api_key):
        """
        Refund a purchase
        """

    def process_purchase(purchase_id, username, token,
                         card_type, cardholder_name, card_expiry,
                         expected_amount=None, api_key=None):
        """
        Process a purchase attempt
        """

    def sync_purchase(purchase_id, username, api_key):
        """
        Sync a purchase attempt
        """

    def get_payment_charge(purchase, username=None):
        """
        Return the payment charge
        """

    def create_token(api_key, card_type, cardholder_name, card_number, card_expiry, card_cvv,
                     street=None, city=None, state=None, zip_code=None, country=None):
        """
        Return a new FDToken
        """
