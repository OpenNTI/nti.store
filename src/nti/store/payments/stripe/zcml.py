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

class IRegisterStripeKeyDirective(interface.Interface):
	"""
	The arguments needed for registering a key
	"""
	alias = fields.TextLine(title="The human readable/writable key alias", required=True)
	private_key = fields.TextLine(title="The private key value. Should not contain spaces",
								  required=True)
	live_mode = fields.Bool(title="Live mode flag", required=False)
	stripe_user_id = fields.TextLine(title="Stripe user id", required=False)
	refresh_token = fields.TextLine(title="Refresh token", required=False)
	public_key = fields.TextLine(title="The public key, Should not contain spaces",
								 required=False)

def registerStripeKey(_context, alias, private_key, live_mode=None, stripe_user_id=None,
					  refresh_token=None, public_key=None):
	"""
	Register a stripe key with the given alias
	"""
	sk = StripeConnectKey(Alias=alias, PrivateKey=private_key, LiveMode=live_mode,
						  StripeUserID=stripe_user_id, RefreshToken=refresh_token,
						  PublicKey=public_key)
	utility(_context, provides=IStripeConnectKey, component=sk, name=alias)
	logger.debug("Stripe key %s has been registered", alias)
