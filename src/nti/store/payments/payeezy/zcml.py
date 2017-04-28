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

from zope.configuration import fields

from nti.base._compat import bytes_

from nti.store.payments.payeezy.interfaces import IPayeezyConnectKey

from nti.store.payments.payeezy.model import PayeezyConnectKey


class IRegisterPayeezyKeyDirective(interface.Interface):
    """
    The arguments needed for registering a key
    """
    provider = fields.TextLine(title=u"The key provider/alias.", required=True)
    api_key = fields.TextLine(title=u"The API key value.", required=True)
    api_secret = fields.TextLine(title=u"The API secret value.", required=True)
    reporting_token = fields.TextLine(title=u"Reporting token", required=False)


def registerPayeezyKey(_context, provider, api_key, api_secret, reporting_token=None):
    """
    Register a Payeezy key with the given alias
    """
    key = PayeezyConnectKey(APIKey=api_key,
                            Provider=provider,
                            APISecret=bytes_(api_secret),
                            ReportingToken=reporting_token)
    utility(_context, provides=IPayeezyConnectKey, component=key, name=provider)
