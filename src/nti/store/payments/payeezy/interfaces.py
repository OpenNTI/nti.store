#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Payeezy Payment interfaces

.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

from zope import interface

from zope.interface.common.mapping import IReadMapping

from nti.schema.field import TextLine
from nti.schema.field import ValidBytesLine


class IPayeezyURLMap(IReadMapping):
    """
    marker interface for URL maps
    """


class IPayeezyConnectKey(interface.Interface):
    Provider = TextLine(title=u"The key name.", required=True)

    APIKey = TextLine(title=u"The api key.", required=True)

    APISecret = ValidBytesLine(title=u"The api secret.", required=True)
    APISecret.setTaggedValue('_ext_excluded_out', True)

    Token = TextLine(title=u"Token.", required=True)
    Token.setTaggedValue('_ext_excluded_out', True)

    JSSecurityKey = TextLine(title=u"The JS security key.", required=False)