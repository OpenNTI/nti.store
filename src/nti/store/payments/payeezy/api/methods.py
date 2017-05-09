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

from nti.store.payments.payeezy.api import requests


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
        return requests.PayeezyHTTPRequests(self.api_key,
                                            self.api_secret,
                                            self.token,
                                            self.url,
                                            self.js_security_key,
                                            self.token_url)

    def authorize(self, amount=None, currency_code=None, description=None,
                  card_type=None, cardholder_name=None, card_number=None,
                  card_expiry=None, card_cvv=None):
        """
        Credit card purchase
        """
        payload = self._make_payload(amount=amount,
                                     currency_code=currency_code,
                                     card_type=card_type,
                                     cardholder_name=cardholder_name,
                                     card_number=card_number,
                                     card_expiry=card_expiry,
                                     card_cvv=card_cvv,
                                     description=description,
                                     transaction_type='authorize')

        return self._make_primary_transaction(payload=payload['payload'])

    def purchase(self, amount=None, currency_code=None, description=None,
                 card_type=None, cardholder_name=None, card_number=None,
                 card_expiry=None, card_cvv=None):
        """
        Credit card purchase
        """
        _make_payload_output = self._make_payload(amount=amount,
                                                  currency_code=currency_code,
                                                  card_type=card_type,
                                                  cardholder_name=cardholder_name,
                                                  card_number=card_number,
                                                  card_expiry=card_expiry,
                                                  card_cvv=card_cvv,
                                                  description=description,
                                                  transaction_type='purchase')
        payload = _make_payload_output['payload']
        payload["partial_redemption"] = "false"  # always
        return self._make_primary_transaction(payload=payload)

    def fd_token(self, card_type=None, cardholder_name=None, card_number=None,
                 card_expiry=None, card_cvv=None, callback=None,
                 street=None, city=None, state=None, zip_code=None, country=None):
        """
        Get an FDToken token
        """

        payload = self._make_fd_token_payload(callback=callback,
                                              card_type=card_type,
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
        return self.payeezy.make_token_get_call(payload)

    def token_payment(self, token, amount, currency_code, card_type, cardholder_name,
                      card_expiry=None,  description=None):
        """
        Process a FDToken token payment
        """
        payload = self._make_token_purchase_payload(token=token,
                                                    amount=amount,
                                                    currency_code=currency_code,
                                                    card_type=card_type,
                                                    cardholder_name=cardholder_name,
                                                    card_expiry=card_expiry,
                                                    description=description)
        self.payload = payload
        return self.payeezy.make_token_post_call(payload)

    def token_refund(self,  token, amount, currency_code, card_type, cardholder_name,
                     card_expiry=None, description=None):
        """
        Process a FDToken token refund
        """
        self.payload = self._make_token_refund_payload(token=token,
                                                       amount=amount,
                                                       currency_code=currency_code,
                                                       card_type=card_type,
                                                       cardholder_name=cardholder_name,
                                                       card_expiry=card_expiry,
                                                       description=description)
        return self.payeezy.make_token_post_call(self.payload)

    def reporting(self, start_date, end_date, searchFor=None):
        payload = self.payload = self._make_reporting_payload(start_date,
                                                              end_date,
                                                              searchFor)
        return self.payeezy.make_reporting_get_call(payload)

    # payload

    def _make_primary_transaction(self, payload):
        self.payload = payload
        return self.payeezy.make_card_based_transaction_post_call(self.payload)

    def _make_payload(self, amount=None, currency_code='USD', description=None,
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

    def _make_fd_token_payload(self, card_type=None, cardholder_name=None, card_number=None,
                               card_expiry=None, card_cvv=None, callback=None,
                               street=None, city=None, state=None, zip_code=None, country=None):

        callback = callback or 'Payeezy.callback'

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
            "callback": callback,
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

    def _make_token_purchase_payload(self, token, amount, currency_code, card_type, cardholder_name,
                                     card_expiry=None,  description=None):

        return self._make_token_payload('purchase',
                                        token=token,
                                        amount=amount,
                                        currency_code=currency_code,
                                        card_type=card_type,
                                        cardholder_name=cardholder_name,
                                        card_expiry=card_expiry,
                                        description=description)

    def _make_token_refund_payload(self, token, amount, currency_code, card_type, cardholder_name,
                                   card_expiry, description=None):

        return self._make_token_payload('refund',
                                        token=token,
                                        amount=amount,
                                        currency_code=currency_code,
                                        card_type=card_type,
                                        cardholder_name=cardholder_name,
                                        card_expiry=card_expiry,
                                        description=description)

    def _make_token_payload(self, transaction_type, token, amount, currency_code, card_type,
                            cardholder_name, card_expiry=None, card_cvv=None,  description=None):

        assert transaction_type is not None, "Transaction type cannot be None"

        assert token is not None, "Token cannot be None"
        if isinstance(token, six.integer_types):
            token = str(token)

        assert amount is not None, "Amount cannot be None"
        if isinstance(amount, six.integer_types):
            amount = str(amount)

        assert currency_code, "Currency cannot be None"
        assert card_type, "Card Type cannot be None"

        if isinstance(card_expiry, six.integer_types):
            card_expiry = str(card_expiry)

        # fill some description
        if description is None:
            msg = "%s transaction for amount: %s"
            description = msg % (card_type, amount)

        assert cardholder_name, "Card holder name was not provided"

        token_data = {
            "type": card_type,
            "value": token,
            "cardholder_name": cardholder_name,
        }
        if card_expiry:
            token_data['exp_date'] = card_expiry

        payload = {
            "merchant_ref": description,
            "transaction_type": transaction_type,
            "method": "token",
            "amount": amount,
            "currency_code": currency_code.upper(),
            "token": {
                "token_type": "FDToken",
                "token_data": token_data
            }
        }
        return payload

    def _make_reporting_payload(self, start_date, end_date, searchFor=None):
        assert start_date, "Start date cannot be None"
        if isinstance(start_date, six.string_types):
            start_date = int(start_date)

        assert end_date, "End date cannot be None"
        if isinstance(end_date, six.string_types):
            end_date = int(end_date)

        payload = {
            "start_date": start_date,
            "end_date": end_date
        }
        if searchFor:
            payload['searchFor'] = searchFor
        return payload
