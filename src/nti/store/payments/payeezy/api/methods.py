#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import six

from zope.cachedescriptors.property import Lazy

from nti.store.payments.payeezy.api import authorization


class Payeezy(object):

    payload = None
    transaction_id = None
    
    def __init__(self, api_key, api_secret, token, url, 
                 js_security_key=None, token_url=None):
        self.token = token
        self.api_key = api_key
        self.api_secret = api_secret
        self.js_security_key = js_security_key
        # urls
        self.url = url
        self.token_url = token_url or url

    @Lazy
    def payeezy(self):
        return authorization.PayeezyHTTPAuthorize(self.api_key,
                                                  self.api_secret,
                                                  self.token,
                                                  self.url,
                                                  self.js_security_key)

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
                 card_expiry=None, card_cvv=None):

        make_payload_output = self.make_payload(amount=amount,
                                                currency_code=currency_code,
                                                card_type=card_type,
                                                cardholder_name=cardholder_name,
                                                card_number=card_number,
                                                card_expiry=card_expiry,
                                                card_cvv=card_cvv,
                                                description=description,
                                                transaction_type='purchase')
        payload = make_payload_output['payload']
        payload["partial_redemption"] = "false"  # always
        return self.make_primary_transaction(payload=payload)

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

    def get_fd_token(self, card_type=None, cardholder_name=None, card_number=None, 
                     card_expiry=None, card_cvv=None,
                     street=None, city=None, state=None, zip_code=None, country=None):

        payload = self.get_fd_token_payload(card_type=card_type, 
                                            cardholder_name=cardholder_name, 
                                            card_number=card_number, 
                                            card_expiry=card_expiry,
                                            card_cvv=card_cvv, 
                                            street=street,
                                            city=city, 
                                            state=state, 
                                            zip_code=zip_code,
                                            country=country)
        payload['apikey'] = self.api_key
        payload['js_security_key'] = self.js_security_key
        self.payload = payload

    # requests

    def make_primary_transaction(self, payload):
        self.payload = payload
        return self.payeezy.make_card_based_transaction_post_call(self.payload)

    def make_secondary_transaction(self, payload, transaction_id):
        self.payload = payload
        self.transaction_id = transaction_id
        return self.payeezy.make_capture_void_refund_post_call(self.payload,
                                                               self.transaction_id)

    def make_payload(self, amount=None, currency_code='USD',  description=None,
                     card_type=None, cardholder_name=None, card_number=None,
                     card_expiry=None, card_cvv=None, transaction_type=None,
                     transaction_tag=None, transaction_id=None):

        assert amount is not None, "Amount cannot be None"
        if isinstance(amount, six.integer_types):
            amount = str(amount)

        assert currency_code, "Currency cannot be None"
        assert transaction_type, "Transaction Type cannot be None"

        # fill some description
        if description is None:
            msg = "%s transaction for amount: %s"
            description = msg % (transaction_type, amount)

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

    def get_fd_token_payload(self, card_type=None, cardholder_name=None, card_number=None, 
                             card_expiry=None, card_cvv=None,
                             street=None, city=None, state=None, zip_code=None, country=None):

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
            "ta_token": "NOIW", 
            "type": "FDToken",
            "callback": 'Payeezy.callback',
            "credit_card.type": card_type,
            "credit_card.cardholder_name": cardholder_name, 
            "credit_card.card_number": card_number,
            "credit_card.exp_date": card_expiry,
            "credit_card.cvv": card_cvv
        }
        if city:
            payload['billing_address.city'] = city
        if country:
            payload['billing_address.country'] = country
        if street:
            payload['billing_address.street'] = street
        if state:
            payload['billing_address.state_province'] = state
        if zip_code is not None:
            payload['billing_address.zip_postal_code'] = str(zip_code)

        return payload
