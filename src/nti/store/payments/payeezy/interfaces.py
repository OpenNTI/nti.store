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
from nti.schema.field import Number
from nti.schema.field import Variant
from nti.schema.field import TextLine
from nti.schema.field import UniqueIterable
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


class IPayeezyTokenException(interface.Interface):
    """
    marker interface for a Payeezy token exception
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
    value = Variant((TextLine(title=u"The token value."),
                     Number(title=u"The token value.")), required=True)
    correlation_id = TextLine(title=u"The correlation id.", required=False)


class IPayeezyPurchaseAttempt(interface.Interface):
    """
    Marker interface for Payeezy purchase attempts
    """
    transaction_id = TextLine(title=u"The transaction id.", required=False)
    transaction_tag = TextLine(title=u"The transaction tag.", required=False)
    correlation_id = TextLine(title=u"The correlation id.", required=False)


class IPayeezyCustomer(interface.Interface):
    """
    Marker interface for Payeezy customers
    """
    Transactions = UniqueIterable(value_type=TextLine(title=u'the transaction id'),
                                  title=u'customer transactions')
