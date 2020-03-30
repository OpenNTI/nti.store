#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division

__docformat__ = "restructuredtext en"

from zope import component

from zope.component.hooks import site

from nti.site.localutility import install_utility

from nti.store.payments.stripe.interfaces import IStripeConnectKeyContainer

from nti.store.payments.stripe.model import StripeConnectKeyContainer

logger = __import__('logging').getLogger(__name__)

STRIPE_CONNECT_KEYS = 'StripeConnectKeys'


def get_stripe_key_container(local_site_manager=None, create=True):
    local_site_manager = local_site_manager or component.getSiteManager()

    container = local_site_manager.queryUtility(IStripeConnectKeyContainer)

    if container is None and create:
        install_stripe_key_container(local_site_manager)
        return local_site_manager.getUtility(IStripeConnectKeyContainer)

    return container


def install_stripe_key_container(local_site_manager):

    if local_site_manager == component.getGlobalSiteManager():
        logger.warn("Skipping attempt to install stripe key container in global site manager.")
        return

    local_site = local_site_manager.__parent__
    assert bool(local_site.__name__), "sites must be named"

    with site(local_site):
        install_utility(StripeConnectKeyContainer(),
                        STRIPE_CONNECT_KEYS,
                        IStripeConnectKeyContainer,
                        local_site_manager)
