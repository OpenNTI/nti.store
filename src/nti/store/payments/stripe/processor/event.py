#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Stripe event functionalilty.

.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import six
import simplejson

from zope.event import notify

from nti.common.maps import CaseInsensitiveDict

from ....store import get_purchase_attempt

from ....interfaces import PurchaseAttemptFailed
from ....interfaces import PurchaseAttemptDisputed
from ....interfaces import PurchaseAttemptRefunded
from ....interfaces import PurchaseAttemptSuccessful

from ..utils import create_payment_charge

from .base import BaseProcessor

class EventProcessor(BaseProcessor):

	events = ("charge.succeeded", "charge.refunded", "charge.failed",
			  "charge.dispute.created", "charge.dispute.updated")

	def _process(self, event, request=None):
		event_type = event.get('type', None)
		data = CaseInsensitiveDict(event.get('data', {}))
		if event_type in self.events:
			data = data.get('metadata') or {}
			purchase_id = data.get('PurchaseID', u'')
			username = data.get('Username', u'')
			purchase = get_purchase_attempt(purchase_id, username)
			if purchase:
				if event_type in ("charge.succeeded") and not purchase.has_succeeded():
					payment_charge = None
					api_key = self.get_api_key(purchase)
					if api_key:
						charges = self.get_charges(purchase_id=purchase_id,
												   start_time=purchase.StartTime,
												   api_key=api_key)
						payment_charge = create_payment_charge(charges[0]) \
							 			 if charges else None
					notify(PurchaseAttemptSuccessful(purchase, payment_charge, request))
				elif event_type in ("charge.refunded") and not purchase.is_refunded():
					notify(PurchaseAttemptRefunded(purchase))
				elif event_type in ("charge.failed") and not purchase.has_failed():
					notify(PurchaseAttemptFailed(purchase))
				elif event_type in ("charge.dispute.created", "charge.dispute.updated") and \
					 not purchase.is_disputed():
					notify(PurchaseAttemptDisputed(purchase))
		else:
			logger.debug('Unhandled event type (%s)' % event_type)

	def _readInput(self, body):
		result = CaseInsensitiveDict()
		try:
			values = simplejson.loads(unicode(body, "utf-8"))
		except UnicodeError:
			values = simplejson.loads(unicode(body, 'iso-8859-1'))
		result.update(values)
		return result

	def process_event(self, body, request=None):
		try:
			event = self._readInput(body) if isinstance(body, six.string_types) else body
			self._process(event, request)
			return True
		except Exception:
			logger.exception('Error processing stripe event (webhook)')
			return False
