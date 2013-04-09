# -*- coding: utf-8 -*-
"""
Store pyramid views.

$Id$
"""
from __future__ import print_function, unicode_literals, absolute_import
__docformat__ = "restructuredtext en"

import six
import time
import gevent
import numbers
import dateutil.parser

from pyramid import httpexceptions as hexc

from zope import component

from pyramid.security import authenticated_userid

from . import purchase_history
from . import purchasable_store
from . import interfaces as store_interfaces
from .payments import pyramid_views as payment_pyramid

class GetPendingPurchasesView(object):

	def __init__(self, request):
		self.request = request

	def __call__(self):
		request = self.request
		username = authenticated_userid(request)
		purchases = purchase_history.get_pending_purchases(username)
		return purchases

class GetPurchaseHistoryView(object):

	def __init__(self, request):
		self.request = request

	def _convert(self, t):
		result = t
		if isinstance(t, six.string_types):
			result = time.mktime(dateutil.parser(t).timetuple())
		return result if isinstance(t, numbers.Number) else None

	def __call__(self):
		request = self.request
		username = authenticated_userid(request)
		start_time = self._convert(request.params.get('startTime', None))
		end_time = self._convert(request.params.get('endTime', None))
		purchases = purchase_history.get_purchase_history(username, start_time, end_time)
		return purchases

class GetPurchaseAttemptView(object):

	def __init__(self, request):
		self.request = request

	def __call__(self):
		request = self.request
		username = authenticated_userid(request)
		purchase_id = request.params.get('purchaseId', None) or request.params.get('OID', None)
		if not purchase_id:
			raise hexc.HTTPBadRequest()
		purchase = purchase_history.get_purchase_attempt(purchase_id, username)
		if purchase is None:
			raise hexc.HTTPNotFound()
		elif purchase.is_pending():
			start_time = purchase.StartTime
			# more than 90 secs try to sync
			if time.time() - start_time >= 90 and not purchase.is_synced():
				def process_sync():
					manager = component.getUtility(store_interfaces.IPaymentProcessor, name=purchase.Processor)
					manager.sync_purchase(purchase_id=purchase_id, username=username)
				gevent.spawn(process_sync)
		return purchase

class GetPurchasablesView(object):

	def __init__(self, request):
		self.request = request

	def __call__(self):
		result = purchasable_store.get_all_purchasables()
		return result

# alias

StripePaymentView = payment_pyramid.StripePaymentView
GetStripeConnectKeyView = payment_pyramid.GetStripeConnectKeyView
