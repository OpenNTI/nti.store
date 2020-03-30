#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
import unittest
from collections import OrderedDict

from hamcrest import assert_that
from hamcrest import has_entries
from hamcrest import starts_with

from six.moves import urllib_parse

from nti.store.payments.stripe.model import StripeConnectConfig

__docformat__ = "restructuredtext en"


class TestStripeConnectConfig(unittest.TestCase):

    def _query_params(self, url):
        url_parts = list(urllib_parse.urlparse(url))
        # Query params are in index 4
        return OrderedDict(urllib_parse.parse_qsl(url_parts[4]))

    def test_stripe_oauth_endpoint_base(self):
        config = StripeConnectConfig(
            StripeOauthBase=b"https://connect.stripe.com/oauth/authorize",
            ClientId="abc123"
        )

        assert_that(config.StripeOauthEndpoint,
                    starts_with("https://connect.stripe.com/oauth/authorize"))
        assert_that(self._query_params(config.StripeOauthEndpoint),
                    has_entries({
                        "response_type": "code",
                        "scope": "read_write",
                        "stripe_landing": "login",
                        "client_id": "abc123"
                    }))

    def test_stripe_oauth_endpoint_with_query(self):
        config = StripeConnectConfig(
            StripeOauthBase=b"https://connect.stripe.com/oauth/authorize?scope=read_only&redirect_uri=uri_one",
            ClientId="abc123"
        )

        assert_that(config.StripeOauthEndpoint,
                    starts_with("https://connect.stripe.com/oauth/authorize"))
        assert_that(self._query_params(config.StripeOauthEndpoint),
                    has_entries({
                        "response_type": "code",
                        "scope": "read_only",
                        "stripe_landing": "login",
                        "client_id": "abc123",
                        "redirect_uri": "uri_one"
                    }))
