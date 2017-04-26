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

import unittest

from nti.externalization.externalization import toExternalObject

from nti.store.payments.payeezy.model import PayeezyConnectKey

from nti.store.tests import SharedConfiguringTestLayer


class TestModel(unittest.TestCase):

    layer = SharedConfiguringTestLayer
    
    def test_external(self):
        key = PayeezyConnectKey(APIKey=u"LIpQyLD7p5FmspOs6pPW9gWG",
                                APISecret=u"3K9VJFyfj0oGIMi7Aeg3HNBp",
                                ReportingToken=u"jBCSE4ACnJBHGItexYhLF8At2PRpLh")
       
        extobj = toExternalObject(key)
        assert_that(extobj, has_key('MimeType'))
        assert_that(extobj, does_not(has_key('APISecret')))
        assert_that(extobj, does_not(has_key('ReportingToken')))
        assert_that(extobj, 
                    has_entry('APIKey', is_(u'LIpQyLD7p5FmspOs6pPW9gWG')))
