#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import has_length
from hamcrest import assert_that

import unittest

from nti.store.utils import from_delimited

from nti.store.utils import ALL_STORE_MIME_TYPES
from nti.store.utils import REGULAR_ATTEMPT_MIME_TYPES
from nti.store.utils import PURCHASE_ATTEMPT_MIME_TYPES

class TestUtils(unittest.TestCase):

	def test_from_delimited(self):
		a = ['tag:nextthought.com,2011-10:CMU-HTML-04630_main.04_630:_computer_science_for_practicing_engineers',
			 'tag:nextthought.com,2011-10:MN-HTML-MiladyCosmetology.cosmetology']
		a = ' '.join(a)
		items = from_delimited(a)
		assert_that(items, has_length(2))

		a = 'tag:nextthought.com,2011-10:MN-HTML-MiladyCosmetology.cosmetology'
		items = from_delimited(a)
		assert_that(items, has_length(1))
		assert_that(items[0], is_(a))

	def test_mime_types(self):
		assert_that(ALL_STORE_MIME_TYPES, has_length(8))
		assert_that(REGULAR_ATTEMPT_MIME_TYPES, has_length(3))
		assert_that(PURCHASE_ATTEMPT_MIME_TYPES, has_length(4))
