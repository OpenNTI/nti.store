#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import none
from hamcrest import is_not
from hamcrest import assert_that
from hamcrest import has_property
does_not = is_not

import fudge
import unittest

from nti.store.payments.payeezy import PayeezyTokenException

from nti.store.payments.payeezy.processor.token import TokenProcessor

from nti.store.tests import SharedConfiguringTestLayer


class TestToken(unittest.TestCase):

    layer = SharedConfiguringTestLayer

    @fudge.patch('nti.store.payments.payeezy.processor.token.TokenProcessor.fd_token',
                 'nti.store.payments.payeezy.processor.token.TokenProcessor.decode_response',)
    def test_valid_token(self, mock_fdt, mock_dcr):
        fake_response = fudge.Fake()
        fake_response.status_code = 200
        fake_data = {
            'results': {
                'avs': 'B',
                'correlation_id': u'124.1493659640325',
                'status': 'success',
                'token': {
                    'cardholder_name': 'IchigoKurosaki',
                    'exp_date': '0930',
                    'type': u'visa',
                    'value': u'1130881202230026'
                },
                'type': 'FDToken'
            },
            'status': 201
        }
        mock_fdt.is_callable().with_args().returns(fake_response)
        mock_dcr.is_callable().with_args().returns(fake_data)
        token = TokenProcessor.get_token("NTI-TEST",
                                         card_type="visa",
                                         cardholder_name="Ichigo Kurosaki",
                                         card_number="4012000033330026",
                                         card_expiry="0930",
                                         card_cvv="019")
        assert_that(token, is_not(none))
        assert_that(token, has_property('type', is_('visa')))
        assert_that(token, has_property('value', is_('1130881202230026')))
        assert_that(token, 
                    has_property('correlation_id', is_('124.1493659640325')))

    @fudge.patch('nti.store.payments.payeezy.processor.token.TokenProcessor.fd_token',)
    def test_invalid_403_response(self, mock_fdt):
        fake_response = fudge.Fake()
        fake_response.status_code = 403
        fake_response.provides('json') \
                     .returns({'message': u'HMAC validation Failure'})

        mock_fdt.is_callable().with_args().returns(fake_response)
        with self.assertRaises(PayeezyTokenException) as e:
            TokenProcessor.get_token("NTI-TEST",
                                     card_type="visa",
                                     cardholder_name="Ichigo Kurosaki",
                                     card_number="4012000033330026",
                                     card_expiry="0930",
                                     card_cvv="019")
            assert_that(e, has_property('status', is_(403)))
            assert_that(e, 
                        has_property('message', is_('HMAC validation Failure')))
            
    @fudge.patch('nti.store.payments.payeezy.processor.token.TokenProcessor.fd_token',
                 'nti.store.payments.payeezy.processor.token.TokenProcessor.decode_response',)
    def test_invalid_card(self, mock_fdt, mock_dcr):
        fake_response = fudge.Fake()
        fake_response.status_code = 200
        fake_data = {
            'results': {
                'status': 'failure',
                'token': {}
            },
            'status': 301
        }
        mock_fdt.is_callable().with_args().returns(fake_response)
        mock_dcr.is_callable().with_args().returns(fake_data)
        mock_fdt.is_callable().with_args().returns(fake_response)
        with self.assertRaises(PayeezyTokenException) as e:
            TokenProcessor.get_token("NTI-TEST",
                                     card_type="visa",
                                     cardholder_name="Ichigo Kurosaki",
                                     card_number="4012000033330026",
                                     card_expiry="0910",
                                     card_cvv="019")
            assert_that(e, has_property('status', is_(301)))
