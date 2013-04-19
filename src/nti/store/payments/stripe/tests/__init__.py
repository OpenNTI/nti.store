#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from nti.store.tests import ConfiguringTestBase as StoreConfiguringTestBase

class ConfiguringTestBase(StoreConfiguringTestBase):
    set_up_packages = StoreConfiguringTestBase.set_up_packages + (('purchasables.zcml', 'nti.store.payments.stripe.tests'),)
