#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import none
from hamcrest import assert_that

import unittest

from nti.dataserver.users import User

from nti.store import get_user

from nti.dataserver.tests.mock_dataserver import WithMockDSTrans

from nti.store.tests import SharedConfiguringTestLayer

class TestStore(unittest.TestCase):

	layer = SharedConfiguringTestLayer

	def _create_user(self, username='nt@nti.com', password='temp001'):
		usr = User.create_user(self.ds, username=username, password=password)
		return usr

	@WithMockDSTrans
	def test_getuser(self):
		created_user = self._create_user()
		user = get_user(created_user)
		assert_that(user, is_(created_user))
		
		user = get_user('nt@nti.com')
		assert_that(user, is_(created_user))
		
		user = get_user(None)
		assert_that(user, is_(none()))
		
		user = get_user('notfound')
		assert_that(user, is_(none()))
