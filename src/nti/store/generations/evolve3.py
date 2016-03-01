#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

generation = 3

from nti.store.generations.install import install_gift_registry

def evolve(context):
    """
    Evolve generation 2 to 3 by registering the gift registry
    """
    logger.info("Store generation %s started", generation)
    install_gift_registry(context)
    logger.info("Store generation %s completed", generation)
