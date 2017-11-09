#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os
import hmac
import time
import hashlib
import binascii
from base64 import b64encode

import simplejson as json

import requests

logger = __import__('logging').getLogger(__name__)

os.urandom(1)


class PayeezyHTTPRequests(object):

    payload = None

    def __init__(self, api_key, api_secret, token, url,
                 js_security_key=None, token_url=None):
        self.token = token
        self.api_key = api_key
        self.api_secret = api_secret
        self.js_security_key = js_security_key
        # urls
        self.url = url
        self.token_url = token_url or url
        # cryptographically strong random number
        self.nonce = str(int(binascii.hexlify(os.urandom(16)), 16))
        self.timestamp = str(int(round(time.time() * 1000)))
        # timeout
        self.timeout = 30

    def generate_hmac_authentication_header(self, payload):
        message_data = self.api_key + self.nonce + self.timestamp + self.token + payload
        hmacInHex = hmac.new(self.api_secret,
                             msg=message_data,
                             digestmod=hashlib.sha256)
        hmacInHex = hmacInHex.hexdigest().encode('ascii')
        return b64encode(hmacInHex)

    def session(self):
        result = requests.Session()
        result.verify = False  # for now
        return result

    # Generic method to make calls for primary transactions
    def make_card_based_transaction_post_call(self, payload):
        response = self.session()
        self.payload = json.dumps(payload)
        authorization = self.generate_hmac_authentication_header(self.payload)
        result = response.post(self.url,
                               headers={
                                   'Content-type': 'application/json',
                                   'apikey': self.api_key,
                                   'token': self.token,
                                   'nonce': self.nonce,
                                   'timestamp': self.timestamp,
                                   'Authorization': authorization
                               },
                               data=self.payload)
        return result

    # Generic method to make calls for secondary transactions
    def make_capture_void_refund_post_call(self, payload, transaction_id):
        response = self.session()
        self.url = self.url + '/' + transaction_id
        self.payload = json.dumps(payload)
        authorization = self.generate_hmac_authentication_header(self.payload)
        result = response.post(self.url,
                               headers={
                                   'Content-type': 'application/json',
                                   'apikey': self.api_key,
                                   'token': self.token,
                                   'nonce': self.nonce,
                                   'timestamp': self.timestamp,
                                   'Authorization': authorization
                               },
                               data=self.payload)
        return result

    def make_token_get_call(self, payload):
        response = self.session()
        self.payload = payload
        result = response.get(self.token_url, params=self.payload)
        return result

    def make_token_post_call(self, payload):
        response = self.session()
        self.payload = json.dumps(payload)
        authorization = self.generate_hmac_authentication_header(self.payload)
        result = response.post(self.url,  # transaction
                               headers={
                                   'Content-type': 'application/json',
                                   'apikey': self.api_key,
                                   'token': self.token,
                                   'nonce': self.nonce,
                                   'timestamp': self.timestamp,
                                   'Authorization': authorization},
                               data=self.payload)
        return result

    def make_reporting_get_call(self, payload):
        response = self.session()
        self.payload = json.dumps(payload)
        authorization = self.generate_hmac_authentication_header(self.payload)
        result = response.get(self.url,
                              headers={
                                  'Content-type': 'application/json',
                                  'apikey': self.api_key,
                                  'token': self.token,
                                  'nonce': self.nonce,
                                  'timestamp': self.timestamp,
                                  'Authorization': authorization
                              },
                              params=payload)
        return result
