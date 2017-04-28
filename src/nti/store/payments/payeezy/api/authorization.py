#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import os
import ssl
import hmac
import time
import hashlib
import binascii
from base64 import b64encode

import simplejson as json

import requests

from requests.adapters import HTTPAdapter

from requests.packages.urllib3.poolmanager import PoolManager


class TLSv1Adapter(HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = PoolManager(num_pools=connections,
                                       maxsize=maxsize,
                                       block=block,
                                       ssl_version=ssl.PROTOCOL_TLSv1)


class PayeezyHTTPAuthorize(object):

    def __init__(self, api_key, api_secret, token, url, token_url=None):
        self.token = token
        self.api_key = api_key
        self.api_secret = api_secret
        # urls
        self.url = url
        self.token_url = token_url or url
        # cryptographically strong random number
        self.nonce =  str(int(binascii.hexlify(os.urandom(16)), 16))
        self.timestamp = str(int(round(time.time() * 1000)))
        # timeout
        self.timeout = 30

    # HMAC Generation
    def generate_hmac_authentication_header(self, payload):
        message_data = self.api_key + self.nonce + self.timestamp + self.token + payload
        hmacInHex = hmac.new(self.api_secret, msg=message_data, digestmod=hashlib.sha256)
        hmacInHex = hmacInHex.hexdigest().encode('ascii')
        return b64encode(hmacInHex)

    # method to make calls for getToken
    def get_token_post_call(self, payload):
        response = requests.Session()
        # response.mount('https://', TLSv1Adapter())
        self.payload = json.dumps(payload)
        authorization = self.generate_hmac_authentication_header(self.payload)
        result = response.post(self.token_url,
                               headers={
                                    'Content-type': 'application/json',
                                    'apikey': self.api_key,
                                    'token': self.token,
                                    'Authorization': authorization},
                               data=self.payload)
        return result

    # Generic method to make calls for primary transactions
    def make_card_based_transaction_post_call(self, payload):
        response = requests.Session()
        self.payload = json.dumps(payload)
        authorization = self.generate_hmac_authentication_header(self.payload)
        result = response.post(self.url,
                               headers= {
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
    def make_capture_void_refund_post_call(self, payload, transactionID):
        response = requests.Session()
        response.mount('https://', TLSv1Adapter())
        self.url = self.url + '/' + transactionID
        self.payload = json.dumps(payload)
        authorization = self.generate_hmac_authentication_header(self.payload)
        result = response.post(self.url,
                               headers={'User-Agent': 'Payeezy-Python',
                                        'content-type': 'application/json',
                                        'api_key': self.api_key,
                                        'token': self.token,
                                        'nonce': self.nonce,
                                        'timestamp': self.timestamp,
                                        'Authorization': authorization},
                               data=self.payload)
        return result
