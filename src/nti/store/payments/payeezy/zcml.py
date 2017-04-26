#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from zope.component.zcml import utility


class IRegisterPayeezyKeyDirective(interface.Interface):
    """
    The arguments needed for registering a key
    """


def registerPayeezyKey(_context):
    """
    Register a Payeezy key with the given alias
    """
    utility(_context, provides=None, component=None, name='')
    logger.debug("Payeezy key %s has been registered")
