#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

generation = 6

from zope.component.hooks import site, setHooks

from zope.annotation.interfaces import IAnnotations

from nti.dataserver.interfaces import IUser

from ..store import get_purchase_history_annotation_key

def do_evolve(context, generation=generation):
	logger.info("Store evolution %s started", generation);

	setHooks()
	conn = context.connection
	ds_folder = conn.root()['nti.dataserver']
	annotation_key = get_purchase_history_annotation_key()
	
	with site(ds_folder):
		users = ds_folder['users']
		for user in users.values():
			if not IUser.providedBy(user):
				continue
			annotations = IAnnotations(user)
			if annotation_key in annotations:
				pass

	logger.info('Store evolution %s done', generation)

def evolve(context):
	"""
	Evolve to generation 6 by updating purchase storage
	"""
	do_evolve(context)
