#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

from zope.security.permission import Permission

logger = __import__('logging').getLogger(__name__)

ACT_LINK_STRIPE = Permission('nti.actions.stripe_connect.link')
