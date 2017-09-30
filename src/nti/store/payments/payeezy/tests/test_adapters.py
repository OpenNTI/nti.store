#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import none
from hamcrest import is_in
from hamcrest import is_not
from hamcrest import assert_that
from hamcrest import has_entries
from hamcrest import has_properties
does_not = is_not

from nti.testing.matchers import validly_provides
from nti.testing.matchers import verifiably_provides

import unittest

from zope import interface

from nti.dataserver.users.users import User

from nti.externalization.externalization import toExternalObject

from nti.store.payments.payeezy.interfaces import IPayeezyError
from nti.store.payments.payeezy.interfaces import IPayeezyCustomer
from nti.store.payments.payeezy.interfaces import IPayeezyPurchaseError
from nti.store.payments.payeezy.interfaces import IPayeezyOperationError
from nti.store.payments.payeezy.interfaces import IPayeezyPurchaseAttempt

from nti.store.payments.payeezy import PayeezyException

from nti.store.purchase_attempt import PurchaseAttempt

from nti.dataserver.tests.mock_dataserver import WithMockDSTrans

from nti.store.tests import SharedConfiguringTestLayer


class TestAdapters(unittest.TestCase):

    layer = SharedConfiguringTestLayer

    @WithMockDSTrans
    def test_customer(self):
        usr = User.create_user(self.ds, username=u"ichigo")
        customer = IPayeezyCustomer(usr, None)
        assert_that(customer, is_not(none()))
        assert_that(customer, validly_provides(IPayeezyCustomer))
        assert_that(customer, verifiably_provides(IPayeezyCustomer))
        customer.Transactions.add('shikai')
        assert_that('shikai', is_in(customer))

    def test_purchase_attempt(self):
        attempt = PurchaseAttempt()
        attempt = IPayeezyPurchaseAttempt(attempt, None)
        assert_that(attempt, is_not(none()))

    def test_string_errors(self):
        error = IPayeezyPurchaseError(u'ichigo', None)
        assert_that(error, is_not(none()))
        assert_that(error, validly_provides(IPayeezyPurchaseError))
        assert_that(error, verifiably_provides(IPayeezyPurchaseError))
        ext_obj = toExternalObject(error)
        assert_that(ext_obj,
                    has_entries('MimeType', 'application/vnd.nextthought.store.payeezypurchaseerror',
                                'Message', 'ichigo',
                                'Type', 'PurchaseError',
                                'Class', 'PayeezyPurchaseError'))

        error = IPayeezyOperationError(u'ichigo', None)
        assert_that(error, is_not(none()))
        assert_that(error, validly_provides(IPayeezyOperationError))
        assert_that(error, verifiably_provides(IPayeezyOperationError))
        ext_obj = toExternalObject(error)
        assert_that(ext_obj,
                    has_entries('MimeType', 'application/vnd.nextthought.store.payeezyoperationerror',
                                'Message', 'ichigo',
                                'Type', 'OperationError',
                                'Class', 'PayeezyOperationError'))

    def test_payeezy_error(self):

        @interface.implementer(IPayeezyError)
        class O(object):
            args = (u'Ichigo',)
            status = 403

        o = O()
        error = IPayeezyOperationError(o, None)
        assert_that(error, is_not(none()))
        assert_that(error, has_properties('Status', is_(403),
                                          'Message', is_('Ichigo')))

    def test_payeezy_exception(self):
        ex = PayeezyException(u'Ichigo')
        ex.status = 403
        error = IPayeezyOperationError(ex, None)
        assert_that(error, is_not(none()))
        assert_that(error, has_properties('Status', is_(403),
                                          'Message', is_('Ichigo')))
