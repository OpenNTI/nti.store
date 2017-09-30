#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import none
from hamcrest import is_not
from hamcrest import assert_that
from hamcrest import has_property
does_not = is_not

from nti.testing.matchers import validly_provides
from nti.testing.matchers import verifiably_provides

from zope import component

from nti.store.payments.payeezy.interfaces import IPayeezyConnectKey

import nti.testing.base

ZCML_STRING = u"""
<configure  xmlns="http://namespaces.zope.org/zope"
            xmlns:i18n="http://namespaces.zope.org/i18n"
            xmlns:zcml="http://namespaces.zope.org/zcml"
            xmlns:payeezy="http://nextthought.com/ntp/payeezy">

    <include package="zope.component" file="meta.zcml" />
    <include package="zope.security" file="meta.zcml" />
    <include package="zope.component" />
    <include package="." file="meta.zcml" />

    <payeezy:registerPayeezyKey
        provider="NTI"
        api_key="LIpQyLD7p5FmspOs6pPW9gWG"
        api_secret="PRJEOy95OA5fNURGcAZ9OgQ"
        token="UgM2hVJjZqEDgSUHEBVTgmUW0r100"
        js_security_key="b9d0ee63dbf511a1902" />

</configure>
"""


class TestZcml(nti.testing.base.ConfiguringTestBase):

    def test_registration(self):
        self.configure_string(ZCML_STRING)

        key = component.queryUtility(IPayeezyConnectKey, name="NTI")
        assert_that(key, is_not(none()))
        assert_that(key, validly_provides(IPayeezyConnectKey))
        assert_that(key, verifiably_provides(IPayeezyConnectKey))
        
        assert_that(key, 
                    has_property('Provider', is_("NTI")))
        
        assert_that(key, 
                    has_property('APIKey', is_("LIpQyLD7p5FmspOs6pPW9gWG")))

        assert_that(key, 
                    has_property('APISecret', is_("PRJEOy95OA5fNURGcAZ9OgQ")))
        
        assert_that(key, 
                    has_property('Token', is_("UgM2hVJjZqEDgSUHEBVTgmUW0r100")))
        
        assert_that(key, 
                    has_property('JSSecurityKey', is_("b9d0ee63dbf511a1902")))
