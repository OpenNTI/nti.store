#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

generation = 9

from zope.catalog.interfaces import ICatalog

from zope.component.hooks import site
from zope.component.hooks import setHooks

from zope.intid.interfaces import IIntIds

from nti.externalization.oids import to_external_ntiid_oid

from nti.invitations.interfaces import IInvitationsContainer

from nti.store.interfaces import IPurchaseAttempt
from nti.store.interfaces import IRedeemedPurchaseAttempt
from nti.store.interfaces import IInvitationPurchaseAttempt

from nti.store.invitations import create_store_purchase_invitation

from nti.store.purchase_index import IX_MIMETYPE
from nti.store.purchase_index import CATALOG_NAME

from nti.store.store import get_purchase_by_code

from nti.store.utils import REDEEM_PURCHASE_ATTEMPT_MIME_TYPE

from nti.zope_catalog.catalog import ResultSet

def get_purchases(catalog, intids):
	doc_ids = catalog[IX_MIMETYPE].apply({'any_of': (REDEEM_PURCHASE_ATTEMPT_MIME_TYPE,)})
	result = ResultSet(doc_ids, intids, True)
	return result

def do_evolve(context, generation=generation):
	logger.info("Store evolution %s started", generation);

	count = 0
	setHooks()
	conn = context.connection
	ds_folder = conn.root()['nti.dataserver']

	with site(ds_folder):
		lsm = ds_folder.getSiteManager()
		intids = lsm.getUtility(IIntIds)
		invitations = lsm.getUtility(IInvitationsContainer)
		catalog = lsm.getUtility(ICatalog, name=CATALOG_NAME)
		for purchase in get_purchases(catalog, intids):
			if not IRedeemedPurchaseAttempt.providedBy(purchase):
				continue
			source = get_purchase_by_code(purchase.RedemptionCode)
			if not IPurchaseAttempt.providedBy(source):
				continue
			purchase.SourcePurchaseID = to_external_ntiid_oid(source)
			if not IInvitationPurchaseAttempt.providedBy(source):
				continue
			invitation = create_store_purchase_invitation(source, purchase.creator)
			invitation.redeemed_purchase = purchase
			invitation.createdTime = purchase.createdTime
			invitation.updateLastMod(purchase.lastModified)
			invitations.add(invitation)
			count += 1

	logger.info('Store evolution %s done. %s items migrated', generation, count)

def evolve(context):
	"""
	Evolve to generation 9 by creating invitations for redeemed purchases
	"""
	do_evolve(context)
