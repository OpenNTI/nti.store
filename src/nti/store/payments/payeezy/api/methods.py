#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import six

from nti.store.payments.payeezy.api import authorization


class Payeezy(object):

    def __init__(self, api_key, api_secret, token, url, token_url):
        self.token = token
        self.api_key = api_key
        self.api_secret = api_secret
        # urls
        self.url = url
        self.token_url = token_url

    def authorize(self, amount=None, currency_code=None, description=None,
                  card_type=None, cardholder_name=None, card_number=None,
                  card_expiry=None, card_cvv=None):

        make_payload_output = self.make_payload(amount=amount,
                                                currency_code=currency_code,
                                                card_type=card_type,
                                                cardholder_name=cardholder_name,
                                                card_number=card_number,
                                                card_expiry=card_expiry,
                                                card_cvv=card_cvv,
                                                description=description,
                                                transaction_type='authorize')

        return self.make_primary_transaction(payload=make_payload_output['payload'])

    def purchase(self, amount=None, currency_code=None, description=None,
                 card_type=None, cardholder_name=None, card_number=None,
                 card_expiry=None, card_cvv=None, ):

        make_payload_output = self.make_payload(amount=amount,
                                                currency_code=currency_code,
                                                card_type=card_type,
                                                cardholder_name=cardholder_name,
                                                card_number=card_number,
                                                card_expiry=card_expiry,
                                                card_cvv=card_cvv,
                                                description=description,
                                                transaction_type='purchase')

        return self.make_primary_transaction(payload=make_payload_output['payload'])

    def capture(self, amount=None, currency_code=None, description=None,
                transaction_tag=None, transaction_id=None):

        make_payload_output = self.make_payload(amount=amount,
                                                currency_code=currency_code,
                                                transaction_tag=transaction_tag,
                                                transaction_id=transaction_id,
                                                description=description,
                                                transaction_type='capture')

        return self.make_secondary_transaction(payload=make_payload_output['payload'],
                                               transaction_id=make_payload_output['transaction_id'])

    def void(self,  payload):
        self.payload = payload
        self.transaction_type = "void"
        return self.make_secondary_transaction(self.transaction_type, self.payload)

    def refund(self,  payload):
        self.payload = payload
        self.transaction_type = "refund"
        return self.make_secondary_transaction(self.transaction_type, self.payload)

    def make_primary_transaction(self, payload):
        self.payload = payload
        self.payeezy = authorization.PayeezyHTTPAuthorize(self.api_key, 
                                                          self.api_secret,
                                                          self.token, 
                                                          self.url, 
                                                          self.tokenurl)
        return self.payeezy.make_card_based_transaction_post_call(self.payload)

    def make_secondary_transaction(self, payload, transaction_id):
        self.payload = payload
        self.transaction_id = transaction_id
        self.payeezy = authorization.PayeezyHTTPAuthorize(self.api_key, 
                                                          self.api_secret, 
                                                          self.token, 
                                                          self.url, 
                                                          self.tokenurl)
        return self.payeezy.make_capture_void_refund_post_call(self.payload, 
                                                               self.transaction_id)

    def make_payload(self, amount=None, currency_code='USD',  description=None,
                     card_type=None, cardholder_name=None, card_number=None,
                     card_expiry=None, card_cvv=None, transaction_type=None,
                     transaction_tag=None, transaction_id=None):

        assert amount is not None, "Amount cannot be None"
        if isinstance(object, six.integer_types):
            amount = str(amount)

        assert currency_code, "Currency cannot be None"
        assert transaction_type, "Transaction Type cannot be None"

        # fill some description
        if description is None:
            description = transaction_type + 'transaction for amount: ' + amount

        if transaction_type in ('authorize', 'purchase'):
            assert card_number is not None, "Card number cannot be None"
            if isinstance(card_number, six.integer_types):
                card_number = str(card_number)

            assert cardholder_name, "Card name was not provided"

            assert card_cvv is not None, "CVV number cannot be None"
            if isinstance(card_cvv, six.integer_types):
                card_cvv = str(card_cvv)

            assert card_expiry is not None, "Expiry cannot be None"
            if isinstance(card_expiry, six.integer_types):
                card_expiry = str(card_expiry)

            payload = {
                "merchant_ref": description,
                "transaction_type": transaction_type,
                "method": "credit_card",
                "amount": amount,
                "currency_code": currency_code.upper(),
                "credit_card": {
                    "type": card_type,
                    "cardholder_name": cardholder_name,
                    "card_number": card_number,
                    "exp_date": card_expiry,
                    "cvv": card_cvv
                }
            }
        else:
            assert transaction_id, "Transaction ID cannot be None"
            assert transaction_tag, "Transaction Tag cannot be None"
            if isinstance(transaction_tag, six.integer_types):
                transaction_tag = str(transaction_tag)

            payload = {
                "merchant_ref": description,
                "transaction_tag": transaction_tag,
                "transaction_type": transaction_type,
                "method": "credit_card", "amount": amount,
                "currency_code": currency_code.upper()
            }

        return {'payload': payload, 'transaction_id': transaction_id}
