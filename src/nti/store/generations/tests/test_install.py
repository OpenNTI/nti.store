#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import has_key
from hamcrest import assert_that

import unittest

from nti.dataserver.tests import mock_dataserver
from nti.dataserver.tests.mock_dataserver import WithMockDSTrans

from nti.store.tests import SharedConfiguringTestLayer


class TestFunctionalInstall(unittest.TestCase):

    layer = SharedConfiguringTestLayer

    @WithMockDSTrans
    def test_installed(self):
        conn = mock_dataserver.current_transaction
        root = conn.root()
        generations = root['zope.generations']
        assert_that(generations, has_key('nti.dataserver-store'))
