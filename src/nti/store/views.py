#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Store pyramid views.

.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from . import MessageFactory as _

import six
import time
import gevent
import numbers
import itertools
import dateutil.parser

from pyramid import httpexceptions as hexc

from zope import component

from nti.dataserver import interfaces as nti_interfaces

from nti.externalization.interfaces import LocatedExternalDict

from . import utils
from . import priceable
from . import enrollment
from . import invitations
from . import purchasable
from . import purchase_history
from . import InvalidPurchasable
from . import interfaces as store_interfaces
from .payments import views as payment_views

# bwc
is_valid_pve_int = utils.is_valid_pve_int
raise_field_error = utils.raise_field_error
is_valid_timestamp = utils.is_valid_timestamp

class _PurchaseAttemptView(object):

	def __init__(self, request):
		self.request = request

	def _last_modified(self, purchases):
		result = 0
		for pa in purchases or ():
			result = max(result, getattr(pa, "lastModified", 0))
		return result

class GetPendingPurchasesView(_PurchaseAttemptView):

	def __call__(self):
		request = self.request
		username = request.authenticated_userid
		purchases = purchase_history.get_pending_purchases(username)
		result = LocatedExternalDict({'Items': purchases,
									  'Last Modified':self._last_modified(purchases)})
		return result

class GetPurchaseHistoryView(_PurchaseAttemptView):

	def _convert(self, t):
		result = t
		if is_valid_timestamp(t):
			result = float(t)
		elif isinstance(t, six.string_types):
			result = time.mktime(dateutil.parser(t).timetuple())
		return result if isinstance(t, numbers.Number) else None

	def __call__(self):
		request = self.request
		username = request.authenticated_userid
		purchasable_id = request.params.get('purchasableID', None)
		if not purchasable_id:
			start_time = self._convert(request.params.get('startTime', None))
			end_time = self._convert(request.params.get('endTime', None))
			purchases = purchase_history.get_purchase_history(username,
															  start_time, end_time)
		else:
			purchases = purchase_history.get_purchase_history_by_item(username,
																	  purchasable_id)
		result = LocatedExternalDict({'Items': purchases,
									  'Last Modified':self._last_modified(purchases)})
		return result

def _sync_purchase(purchase):
	purchase_id = purchase.id
	username = purchase.creator.username

	def sync_purchase():
		manager = component.getUtility(store_interfaces.IPaymentProcessor,
									   name=purchase.Processor)
		manager.sync_purchase(purchase_id=purchase_id, username=username)

	def process_sync():
		component.getUtility(nti_interfaces.IDataserverTransactionRunner)(sync_purchase)

	gevent.spawn(process_sync)

class GetPurchaseAttemptView(object):

	def __init__(self, request):
		self.request = request

	def __call__(self):
		request = self.request
		username = request.authenticated_userid
		purchase_id = request.params.get('purchaseID')
		if not purchase_id:
			raise_field_error(request, "purchaseID",
							  _("Must specify a valid purchase attempt id"))

		purchase = purchase_history.get_purchase_attempt(purchase_id, username)
		if purchase is None:
			raise hexc.HTTPNotFound(detail=_('Purchase attempt not found'))
		elif purchase.is_pending():
			start_time = purchase.StartTime
			if time.time() - start_time >= 90 and not purchase.is_synced():
				_sync_purchase(purchase)

		result = LocatedExternalDict({'Items':[purchase],
									  'Last Modified':purchase.lastModified})
		return result

from pyramid.authorization import ACLAuthorizationPolicy
from nti.dataserver.authorization import ACT_READ

class GetPurchasablesView(object):

	def __init__(self, request):
		self.request = request

	def __call__(self):
		purchasables = list(purchasable.get_all_purchasables())
		for p in list(purchasables):
			if hasattr(p, 'HACK_make_acl'):
				acl = p.HACK_make_acl()
				class Dummy(object):
					__acl__ = None
				dummy = Dummy()
				dummy.__acl__ = acl
				policy = ACLAuthorizationPolicy()
				principals = self.request.effective_principals
				if not policy.permits(dummy, principals, ACT_READ):
					logger.debug('Removing purch %s', p)
					purchasables.remove(p)

		result = LocatedExternalDict({'Items': purchasables, 'Last Modified':0})
		return result

class GetCoursesView(GetPurchasablesView):

	def __call__(self):
		result = super(GetCoursesView,self).__call__()
		purchasables = result['Items']
		courses = list(itertools.ifilter(store_interfaces.ICourse.providedBy,
										 purchasables))
		result['Items'] = courses
		return result

# post - views

_PostView = utils.AbstractPostView

class RedeemPurchaseCodeView(_PostView):

	def __call__(self):
		request = self.request
		values = self.readInput()
		purchasable_id = values.get('purchasableID')
		if not purchasable_id:
			raise_field_error(request, "purchasableID",
							  _("Must specify a valid purchasable id"))

		invitation_code = values.get('invitationCode', values.get('invitation_code'))
		if not invitation_code:
			raise_field_error(request, "invitation_code",
							  _("Must specify a valid invitation code"))

		purchase = invitations.get_purchase_by_code(invitation_code)
		if purchase is None or not store_interfaces.IPurchaseAttempt.providedBy(purchase):
			raise hexc.HTTPNotFound(detail=_('Purchase attempt not found'))

		if purchase.Quantity is None:
			raise hexc.HTTPUnprocessableEntity(detail=_('Not redeemable purchase'))

		if purchasable_id not in purchase.Items:
			raise_field_error(request, "invitation_code",
							  _("The invitation code is not for this purchasable"))

		username = request.authenticated_userid
		try:
			invite = \
				invitations.create_store_purchase_invitation(purchase, invitation_code)
			invite.accept(username)
		except invitations.InvitationAlreadyAccepted:
			raise_field_error(request, "invitation_code",
							  _("The invitation code has already been accepted"))
		except invitations.InvitationCapacityExceeded:
			raise_field_error(request, "invitation_code",
							  _("There are no remaining invitations for this code"))

		return hexc.HTTPNoContent()

class PricePurchasableView(_PostView):

	def price(self, purchasable_id, quantity):
		pricer = component.getUtility(store_interfaces.IPurchasablePricer)
		source = priceable.create_priceable(purchasable_id, quantity)
		result = pricer.price(source)
		return result

	def price_purchasable(self, values=None):
		values = values or self.readInput()
		purchasable_id = values.get('purchasableID', u'')

		# check quantity
		quantity = values.get('quantity', 1)
		if not is_valid_pve_int(quantity):
			raise_field_error(self.request, 'quantity', _('Invalid quantity'))
		quantity = int(quantity)

		try:
			result = self.price(purchasable_id, quantity)
			return result
		except InvalidPurchasable:
			raise_field_error(self.request, 'purchasableID', _('Purchasable not found'))

	def __call__(self):
		result = self.price_purchasable()
		return result

class EnrollCourseView(_PostView):

	def enroll(self, values=None):
		values = values or self.readInput()
		username = self.request.authenticated_userid
		course_id = values.get('courseID', u'')
		description = values.get('description', u'')
		try:
			enrollment.enroll_course(username, course_id, description, self.request)
		except enrollment.CourseNotFoundException:
			raise_field_error(self.request, 'courseID', _('Course not found'))

		return hexc.HTTPNoContent()

	def __call__(self):
		result = self.enroll()
		return result

class UnenrollCourseView(_PostView):

	def unenroll(self, values=None):
		values = values or self.readInput()
		username = self.request.authenticated_userid
		course_id = values.get('courseID', u'')
		try:
			enrollment.unenroll_course(username, course_id, self.request)
		except enrollment.CourseNotFoundException:
			logger.error("Course %s not found" % course_id)
			raise_field_error(self.request, 'courseID', _('Course not found'))
		except enrollment.UserNotEnrolledException:
			logger.error("User %s not enrolled in %s" % (username, course_id))
			raise_field_error(self.request, 'username', _('User not enrolled'))
		except enrollment.InvalidEnrollmentAttemptException:
			raise_field_error(self.request, 'courseID', _('Invalid enrollment attempt'))

		return hexc.HTTPNoContent()

	def __call__(self):
		result = self.unenroll()
		return result

# alias

StripePaymentView = payment_views.StripePaymentView
CreateStripeTokenView = payment_views.CreateStripeTokenView
GetStripeConnectKeyView = payment_views.GetStripeConnectKeyView
StripeRefundPaymentView = payment_views.StripeRefundPaymentView
PricePurchasableWithStripeCouponView = payment_views.PricePurchasableWithStripeCouponView
