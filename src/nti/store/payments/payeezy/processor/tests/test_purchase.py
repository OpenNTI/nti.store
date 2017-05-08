#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import is_in
from hamcrest import is_not
from hamcrest import has_length
from hamcrest import assert_that
from hamcrest import has_property
does_not = is_not

import fudge
import unittest

from zope.component import eventtesting

from nti.dataserver.users import User

from nti.store.interfaces import PA_STATE_SUCCESS
from nti.store.interfaces import IPurchaseAttemptStarted
from nti.store.interfaces import IPurchaseAttemptSuccessful

from nti.store.payments.payeezy.interfaces import IPayeezyCustomer
from nti.store.payments.payeezy.interfaces import IPayeezyPurchaseAttempt

from nti.store.payments.payeezy.processor.purchase import PurchaseProcessor

from nti.store.purchase_history import get_purchase_attempt

from nti.dataserver.tests import mock_dataserver

from nti.store.tests import SharedConfiguringTestLayer

from nti.store.payments.payeezy.processor.tests import create_user
from nti.store.payments.payeezy.processor.tests import create_and_register_purchase_attempt


class TestPurchase(unittest.TestCase):

    layer = SharedConfiguringTestLayer

    ntiid = u'tag:nextthought.com,2011-10:NextThought-purchasable-HelpCenter'

    @fudge.patch('nti.store.payments.payeezy.processor.purchase.token_payment')
    @mock_dataserver.WithMockDSTrans
    def test_valid_purchase(self, mock_fdt):
        fake_response = fudge.Fake()
        fake_response.status_code = 201
        fake_data = {
            'amount': '100',
            'bank_message': 'Approved',
            'bank_resp_code': '100',
            'correlation_id': '124.1493661575888',
            'currency': u'USD',
            'cvv2': 'I',
            'gateway_message': u'Transaction Normal',
            'gateway_resp_code': u'00',
            'method': 'token',
            'token': {
                'token_data': {
                    'cardholder_name': u'Ichigo Kurosaki',
                    'exp_date': '0930',
                    'type': u'visa',
                    'value': u'7297812665630026'
                },
                'token_type': 'FDToken'
            },
            'transaction_id': u'ET147499',
            'transaction_status': u'approved',
            'transaction_tag': u'150621620',
            'transaction_type': u'purchase',
            'validation_status': u'success'
        }
        fake_response.provides('json').returns(fake_data)
        mock_fdt.is_callable().with_args().returns(fake_response)

        username = u'ichigo@bleach.com'
        with mock_dataserver.mock_db_trans(self.ds):
            create_user(username)
            purchase_id = create_and_register_purchase_attempt(username, self.ntiid)
        
        with mock_dataserver.mock_db_trans(self.ds):
            PurchaseProcessor.process_purchase(purchase_id, 
                                               token=u"7297812665630026", 
                                               card_type=u"visa", 
                                               cardholder_name=u'Ichigo Kurosaki', 
                                               card_expiry=u"0930", 
                                               api_key='NTI-TEST',
                                               username=username)
        
       
        with mock_dataserver.mock_db_trans(self.ds):
            pa = get_purchase_attempt(purchase_id, username)
            assert_that(pa, has_property('State', is_(PA_STATE_SUCCESS)))
            pa = IPayeezyPurchaseAttempt(pa)
            assert_that(pa, has_property('token', is_("7297812665630026")))
            assert_that(pa, has_property('transaction_id', is_('ET147499')))
            assert_that(pa, has_property('transaction_tag', is_('150621620')))
            assert_that(pa, has_property('correlation_id', is_('124.1493661575888')))
            
        assert_that(eventtesting.getEvents(IPurchaseAttemptStarted),
                                           has_length(1))

        assert_that(eventtesting.getEvents(IPurchaseAttemptSuccessful),
                                           has_length(1))
        
        with mock_dataserver.mock_db_trans(self.ds):
            user = User.get_user(username)
            customer = IPayeezyCustomer(user)
            assert_that('ET147499', is_in(customer))
