#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=inherit-non-class,expression-not-assigned
from zope import interface

from zope.component.zcml import utility

from zope.configuration.fields import Bool

from zope.schema import TextLine

from nti.common.cypher import get_plaintext

from nti.schema.field import HTTPURL

from nti.store.payments.stripe.interfaces import IStripeConnectConfig
from nti.store.payments.stripe.interfaces import IStripeConnectKey

from nti.store.payments.stripe.model import StripeConnectConfig
from nti.store.payments.stripe.model import StripeConnectKey

logger = __import__('logging').getLogger(__name__)


class IRegisterStripeKeyDirective(interface.Interface):
    """
    The arguments needed for registering a key
    """
    alias = TextLine(title=u"The human readable/writable key alias",
                     required=True)
    private_key = TextLine(title=u"The private key value. Should not contain spaces",
                           required=True)

    live_mode = Bool(title=u"Live mode flag", required=False)

    stripe_user_id = TextLine(title=u"Stripe user id", required=False)

    refresh_token = TextLine(title=u"Refresh token", required=False)

    public_key = TextLine(title=u"The public key, Should not contain spaces",
                          required=False)


class IRegisterStripeConnectDirective(interface.Interface):
    """
    The arguments needed for registering a Stripe Connect config
    """
    client_id = TextLine(title=u"Platform Client ID",
                         description=u"The client id of the platform requesting "
                                     u"authorization.",
                         required=True)

    token_endpoint = HTTPURL(title=u"Stripe Token Endpoint",
                             description=u"The Stripe OAuth endpoint at which the user "
                                         u"authorizes our platform.",
                             required=True)

    deauthorize_endpoint = HTTPURL(title=u"Stripe Deauthorize Endpoint",
                                   description=u"The Stripe endpoint at which the user "
                                               u"deauthorizes our platform.",
                                   required=True)

    completion_route_prefix = TextLine(title=u"Completion Route Prefix",
                                       description=u"The prefix for the route to which the user"
                                                   u" will be directed on authorization "
                                                   u"completion.",
                                       required=True)

    secret_key = TextLine(title=u"Platform Secret Key",
                              description=u"Secret key of the platform requesting authorization.",
                          required=True)

    stripe_oauth_base = HTTPURL(title=u"Stripe OAuth Base",
                                description=u"Base url of Stripe's initial OAuth endpoint.",
                                required=True)


def decode_key(key):
    try:
        return get_plaintext(key)
    except Exception:  # pylint: disable=broad-except
        return key


def registerStripeKey(_context, alias, private_key, live_mode=None, stripe_user_id=None,
                      refresh_token=None, public_key=None):
    """
    Register a stripe key with the given alias
    """
    sk = StripeConnectKey(Alias=alias,
                          LiveMode=live_mode,
                          PublicKey=public_key,
                          StripeUserID=stripe_user_id,
                          PrivateKey=decode_key(private_key),
                          RefreshToken=decode_key(refresh_token),)
    utility(_context, provides=IStripeConnectKey, component=sk, name=alias)


def registerStripeConnect(_context,
                          client_id,
                          token_endpoint,
                          deauthorize_endpoint,
                          completion_route_prefix,
                          secret_key,
                          stripe_oauth_base):
    """
    Register configuration for Stripe Connect
    """
    config = StripeConnectConfig(TokenEndpoint=token_endpoint,
                                 DeauthorizeEndpoint=deauthorize_endpoint,
                                 CompletionRoutePrefix=completion_route_prefix,
                                 SecretKey=decode_key(secret_key),
                                 ClientId=client_id,
                                 StripeOauthBase=stripe_oauth_base)
    utility(_context, provides=IStripeConnectConfig, component=config)
