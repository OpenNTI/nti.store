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

from nti.schema.field import Int
from nti.schema.field import Set
from nti.schema.field import TextLine
from nti.schema.field import ValidBytesLine

from nti.store.interfaces import IPurchaseError
from nti.store.interfaces import IOperationError

FAILED = u'failed'
SUCCESS = u'success'
FAILURE = u'failure'
APPROVED = u'approved'

STATES = (FAILED, FAILURE, APPROVED, SUCCESS)

STATE_VOCABULARY = SimpleVocabulary([SimpleTerm(_x) for _x in STATES])


class IPayeezyException(interface.Interface):
    """
    marker interface for a Payeezy exception
    """


class IPayeezyError(interface.Interface):
    """
    marker interface for all Payeezy errors
    """


class IPayeezyOperationError(IOperationError):
    """
    Marker interface for Payeezy operation errors
    """
    Status = Int(title=u'Status', required=False)


class IPayeezyPurchaseError(IPurchaseError, IPayeezyOperationError):
    """
    Marker interface for Payeezy purchase errors
    """


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


class IPayeezyPurchaseAttempt(interface.Interface):
    """
    Marker interface for Payeezy purchase attempts
    """


class IPayeezyCustomer(interface.Interface):
    """
    Marker interface for Payeezy customers
    """
    Transactions = Set(value_type=TextLine(title=u'the transaction id'),
                       title=u'customer transactions')
