#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import assert_that
from hamcrest import has_property

from nti.testing.matchers import verifiably_provides

from zope import component

from nti.store.interfaces import IPurchasable

import nti.testing.base

HEAD_ZCML_STRING = u"""
<configure xmlns="http://namespaces.zope.org/zope"
           xmlns:zcml="http://namespaces.zope.org/zcml"
           xmlns:pcs="http://nextthought.com/ntp/purchasable"
           i18n_domain='nti.dataserver'>

    <include package="zope.component" />
    <include package="." file="meta.zcml" />

"""

ZCML_STRING = HEAD_ZCML_STRING + u"""
    <pcs:registerPurchasable
        ntiid="tag:nextthought.com,2011-10:PRMIA-purchasable-RiskCourse"
        title="NextThought Help Center"
        provider="NTI-TEST"
        author="NEXTTHOUGHT"
        amount="100"
        currency="USD"
        discountable="False"
        bulk_purchase="True"
        items="tag:nextthought.com,2011-10:PRMIA-HTML-PRMIA_RiskCourse.advanced_stress_testing_for_financial_institutions">

        also here is some text &amp; some more text <![CDATA[<p>html paragraph</p>]]>
    </pcs:registerPurchasable>

</configure>
"""

class TestZcml(nti.testing.base.ConfiguringTestBase):

	def test_registration(self):
		self.configure_packages(('nti.contentfragments',))
		
		self.configure_string(ZCML_STRING)
		
		name = "tag:nextthought.com,2011-10:PRMIA-purchasable-RiskCourse"		
		description = u"also here is some text & some more text <p>html paragraph</p>"
		purchasable = component.getUtility(IPurchasable, name=name)
		assert_that(purchasable, verifiably_provides(IPurchasable))
		assert_that(purchasable, has_property('Description', description))
