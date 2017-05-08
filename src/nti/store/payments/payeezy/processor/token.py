#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import re

import simplejson

from nti.store import MessageFactory as _

from nti.store.payments.payeezy import PayeezyTokenException

from nti.store.payments.payeezy.interfaces import SUCCESS

from nti.store.payments.payeezy.model import PayeezyFDToken

from nti.store.payments.payeezy.processor import get_payeezy


class TokenProcessor(object):

    __callback__ = "callback"

    def _safe_error_message(self, result):
        try:
            data = result.json()
            return data['message']
        except Exception:
            return None

    def _decode_response(self, result):
        text = re.sub(r'[\s\n]', '', result.text)
        text = text[len(self.__callback__) + 1:-1]
        data = simplejson.loads(text)
        return data

    def fd_token(self, payeezy, card_type, cardholder_name, card_number, card_expiry, card_cvv,
                 street=None, city=None, state=None, zip_code=None, country=None):

        return payeezy.fd_token(card_type=card_type,
                                cardholder_name=cardholder_name,
                                card_number=card_number,
                                card_expiry=card_expiry,
                                card_cvv=card_cvv,
                                street=street,
                                city=city,
                                state=state,
                                zip_code=zip_code,
                                country=country,
                                callback=self.__callback__)

    def get_token(self, key, card_type, cardholder_name, card_number, card_expiry, card_cvv,
                  street=None, city=None, state=None, zip_code=None, country=None):
        try:
            payeezy = get_payeezy(key)
            result = self.fd_token(payeezy,
                                   cardholder_name=cardholder_name,
                                   card_number=card_number,
                                   card_expiry=card_expiry,
                                   card_cvv=card_cvv,
                                   street=street,
                                   city=city,
                                   state=state,
                                   zip_code=zip_code,
                                   country=country)
            if result.status_code != 200:
                msg = _("Invalid status code")
                e = PayeezyTokenException(msg)
                e.status = result.status_code
                e.message = self._safe_error_message(result)
                raise e

            data = self._decode_response(result)
            status = data.get('status')
            results = data.get('results') or {}
            token = results.get('token')
            if not token:
                msg = _("Missing token response")
                e = PayeezyTokenException(msg)
                e.status = status
                raise e
            status = results.get('status')
            if status != SUCCESS:
                msg = _("Could not compute token")
                e = PayeezyTokenException(msg)
                e.status = status
                raise e
            correlation_id = results.get('correlation_id')
            result = PayeezyFDToken(type=token['type'],
                                    value=token['value'],
                                    correlation_id=correlation_id)
            return result
        except PayeezyTokenException:
            raise
        except Exception:
            logger.exception("Cannot get FDToken")
            msg = _("Cannot get FDToken")
            e = PayeezyTokenException(msg)
            raise e
