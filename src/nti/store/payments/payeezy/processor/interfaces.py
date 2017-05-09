#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Payeezy Payment Processor interfaces

.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

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
                         api_key, expected_amount=None):
        """
        Process a purchase attempt
        """

    def sync_purchase(purchase_id, username, api_key):
        """
        Sync a purchase attempt
        """
