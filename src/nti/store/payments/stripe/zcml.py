#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from zope.component.zcml import utility

from zope.configuration import fields

from nti.store.payments.stripe.interfaces import IStripeConnectKey

from nti.store.payments.stripe.stripe_key import StripeConnectKey

from nti.utils.cypher import get_plaintext


class IRegisterStripeKeyDirective(interface.Interface):
    """
    The arguments needed for registering a key
    """
    alias = fields.TextLine(title=u"The human readable/writable key alias",
						    required=True)
    private_key = fields.TextLine(title=u"The private key value. Should not contain spaces",
                                  required=True)
    live_mode = fields.Bool(title=u"Live mode flag", required=False)
    stripe_user_id = fields.TextLine(title=u"Stripe user id", required=False)
    refresh_token = fields.TextLine(title=u"Refresh token", required=False)
    public_key = fields.TextLine(title=u"The public key, Should not contain spaces",
                                 required=False)


def registerStripeKey(_context, alias, private_key, live_mode=None, stripe_user_id=None,
                      refresh_token=None, public_key=None):
    """
    Register a stripe key with the given alias
    """
    sk = StripeConnectKey(Alias=alias, 
						  LiveMode=live_mode,
						  PublicKey=public_key,
                          StripeUserID=stripe_user_id,
						  PrivateKey=get_plaintext(private_key),
                          RefreshToken=get_plaintext(refresh_token),)
    utility(_context, provides=IStripeConnectKey, component=sk, name=alias)
    logger.debug("Stripe key %s has been registered", alias)
