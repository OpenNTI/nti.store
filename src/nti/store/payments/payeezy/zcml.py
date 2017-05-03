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

from nti.utils.cypher import get_plaintext


class IRegisterPayeezyKeyDirective(interface.Interface):
    """
    The arguments needed for registering a key
    """
    provider = fields.TextLine(title=u"The key provider/alias.", required=True)
    api_key = fields.TextLine(title=u"The API key value.", required=True)
    api_secret = fields.TextLine(title=u"The API secret value.", required=True)
    js_security_key = fields.TextLine(title=u"The JS security key.", 
                                      required=True)
    token = fields.TextLine(title=u"Reporting token", required=False)


def decode_key(key):
    try:
        return get_plaintext(key)
    except Exception:
        return key


def registerPayeezyKey(_context, provider, api_key, api_secret, token,
                       js_security_key=None):
    """
    Register a Payeezy key with the given alias
    """
    key = PayeezyConnectKey(Token=token,
                            APIKey=api_key,
                            Provider=provider,
                            APISecret=bytes_(decode_key(api_secret)),
                            JSSecurityKey=decode_key(js_security_key))
    utility(_context, provides=IPayeezyConnectKey,
            component=key, name=provider)
