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

from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary

from nti.schema.field import TextLine
from nti.schema.field import ValidBytesLine


FAILED = u'failed'
SUCCESS = u'success'
FAILURE = u'failure'
APPROVED = u'approved'

STATES = (FAILED, FAILURE, APPROVED, SUCCESS)

STATE_VOCABULARY = SimpleVocabulary([SimpleTerm(_x) for _x in STATES])


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


class IPayeezyFDToken(interface.Interface):
    type = TextLine(title=u"The token type name.", required=False)
    value = TextLine(title=u"The token value.", required=True)
