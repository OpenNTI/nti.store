#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import is_not
from hamcrest import has_key
from hamcrest import has_entry
from hamcrest import assert_that
does_not = is_not

from nti.testing.matchers import validly_provides
from nti.testing.matchers import verifiably_provides

import unittest

from nti.externalization.externalization import toExternalObject

from nti.store.payments.payeezy.interfaces import IPayeezyFDToken
from nti.store.payments.payeezy.interfaces import IPayeezyConnectKey

from nti.store.payments.payeezy.model import PayeezyFDToken
from nti.store.payments.payeezy.model import PayeezyConnectKey

from nti.store.tests import SharedConfiguringTestLayer


class TestModel(unittest.TestCase):

    layer = SharedConfiguringTestLayer

    def test_connect_key(self):
        key = PayeezyConnectKey(Provider=u'NTI',
                                APIKey=u"LIpQyLD7p5FmspOs6pPW9gWG",
                                APISecret="3K9VJFyfj0oGIMi7Aeg3HNBp",
                                Token="jBCSE4ACnJBHGItexYhLF8At2PRpLh",
                                JSSecurityKey=u"b9d0ee63Aizendbf511a1902")
        assert_that(key, validly_provides(IPayeezyConnectKey))
        assert_that(key, verifiably_provides(IPayeezyConnectKey))

        extobj = toExternalObject(key)
        assert_that(extobj, has_key('MimeType'))
        assert_that(extobj, does_not(has_key('APISecret')))
        assert_that(extobj, does_not(has_key('Token')))
        assert_that(extobj,
                    has_entry('Provider', is_(u'NTI')))
        assert_that(extobj,
                    has_entry('APIKey', is_(u'LIpQyLD7p5FmspOs6pPW9gWG')))
        assert_that(extobj,
                    has_entry('JSSecurityKey', is_(u'b9d0ee63Aizendbf511a1902')))

    def test_fd_token(self):
        token = PayeezyFDToken(type=u'visa',
                               value=u'123045',
                               correlation_id=u'124.0330')
        assert_that(token, validly_provides(IPayeezyFDToken))
        assert_that(token, verifiably_provides(IPayeezyFDToken))

        extobj = toExternalObject(token)
        assert_that(extobj, has_key('MimeType'))
        assert_that(extobj,
                    has_entry('type', is_(u'visa')))
        assert_that(extobj,
                    has_entry('value', is_(u'123045')))
        assert_that(extobj,
                    has_entry('correlation_id', is_(u'124.0330')))
