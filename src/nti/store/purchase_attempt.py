#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Defines purchase attempt object.

.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import time
import BTrees
from functools import total_ordering

from zope import interface
from zope.container.contained import Contained
from zope.mimetype.interfaces import IContentTypeAware
from zope.annotation.interfaces import IAttributeAnnotatable
from zope.schema.fieldproperty import FieldPropertyStoredThroughField as FP

from nti.dataserver.interfaces import ICreated
from nti.dataserver.datastructures import ModDateTrackingObject

from nti.externalization.externalization import WithRepr
from nti.externalization.oids import to_external_ntiid_oid

from nti.schema.schema import EqHash
from nti.schema.field import SchemaConfigured
from nti.schema.fieldproperty import createDirectFieldProperties

from nti.zodb import minmax
from nti.zodb.persistentproperty import PersistentPropertyHolder

from .utils import MetaStoreObject

from .purchase_order import replace_quantity
from .purchase_order import get_providers as order_providers
from .purchase_order import get_currencies as order_currencies
from .purchase_order import get_purchasables as order_purchasables

from .interfaces import PA_STATE_FAILED
from .interfaces import PA_STATE_FAILURE
from .interfaces import PA_STATE_SUCCESS
from .interfaces import PA_STATE_UNKNOWN
from .interfaces import PA_STATE_STARTED
from .interfaces import PA_STATE_PENDING
from .interfaces import PA_STATE_RESERVED
from .interfaces import PA_STATE_DISPUTED
from .interfaces import PA_STATE_REFUNDED
from .interfaces import PA_STATE_CANCELED

from .interfaces import IPurchaseAttempt
from .interfaces import IRedeemedPurchaseAttempt
from .interfaces import IEnrollmentPurchaseAttempt
from .interfaces import IInvitationPurchaseAttempt

@total_ordering
@interface.implementer(ICreated,
					   IPurchaseAttempt,
					   IAttributeAnnotatable,
					   IContentTypeAware)
@WithRepr
@EqHash("Order", "StartTime", "Processor")
class PurchaseAttempt(ModDateTrackingObject,
					  SchemaConfigured,
					  Contained,
					  PersistentPropertyHolder):

	__external_class_name__ = "PurchaseAttempt"
	__metaclass__ = MetaStoreObject

	createDirectFieldProperties(IPurchaseAttempt)

	@property
	def Items(self):
		return self.Order.NTIIDs

	@property
	def Quantity(self):
		return self.Order.Quantity

	@property
	def id(self):
		return unicode(to_external_ntiid_oid(self))

	@property
	def creator(self):
		result = getattr(self.__parent__, 'user', None)
		return result

	def __str__(self):
		return "%s,%s" % (self.Items, self.State)

	def __lt__(self, other):
		try:
			return self.StartTime < other.StartTime
		except AttributeError:
			return NotImplemented

	def __gt__(self, other):
		try:
			return self.StartTime > other.StartTime
		except AttributeError:
			return NotImplemented

	def has_failed(self):
		return self.State in (PA_STATE_FAILED, PA_STATE_FAILURE, PA_STATE_CANCELED)

	def has_succeeded(self):
		return self.State == PA_STATE_SUCCESS

	def is_unknown(self):
		return self.State == PA_STATE_UNKNOWN

	def is_pending(self):
		return self.State in (PA_STATE_STARTED, PA_STATE_PENDING)

	def is_refunded(self):
		return self.State == PA_STATE_REFUNDED

	def is_disputed(self):
		return self.State == PA_STATE_DISPUTED

	def is_reserved(self):
		return self.State == PA_STATE_RESERVED

	def is_canceled(self):
		return self.State == PA_STATE_CANCELED

	def has_completed(self):
		return not (self.is_pending() or self.is_reserved() or self.is_disputed())

	def is_synced(self):
		return self.Synced

@interface.implementer(IInvitationPurchaseAttempt)
class InvitationPurchaseAttempt(PurchaseAttempt):

	def __init__(self, *args, **kwargs):
		super(PurchaseAttempt, self).__init__(*args, **kwargs)
		self._consumers = BTrees.OOBTree.OOBTree()
		self._tokens = minmax.NumericMinimum(self.Quantity)

	def reset(self):
		self._tokens.value = 0

	def consumerMap(self):
		return dict(self._consumers)

	def register(self, user, linked_purchase_id=None):
		user = getattr(user, "username", user)
		if user and not user in self._consumers:
			self._consumers[user] = linked_purchase_id
			return True
		return False

	@property
	def tokens(self):
		return self._tokens.value

	def restore_token(self):
		if self._tokens.value < self.Quantity:
			self._tokens += 1
			return True
		return False

	def consume_token(self):
		if self._tokens.value > 0:
			self._tokens -= 1
			return True
		return False

	def __str__(self):
		return self.id

@interface.implementer(IRedeemedPurchaseAttempt)
class RedeemedPurchaseAttempt(PurchaseAttempt):
	RedemptionCode = FP(IRedeemedPurchaseAttempt['RedemptionCode'])
	RedemptionTime = FP(IRedeemedPurchaseAttempt['RedemptionTime'])

@interface.implementer(IEnrollmentPurchaseAttempt)
class EnrollmentPurchaseAttempt(PurchaseAttempt):
	Processor = FP(IEnrollmentPurchaseAttempt['Processor'])

def get_providers(purchase):
	return order_providers(purchase.Order)

def get_currencies(purchase):
	return order_currencies(purchase.Order)

def get_purchasables(purchase):
	return order_purchasables(purchase.Order)

def create_purchase_attempt(order, processor, state=None, description=None, 
							start_time=None):
	state = state or PA_STATE_UNKNOWN
	start_time = start_time if start_time else time.time()
	cls = PurchaseAttempt if not order.Quantity else InvitationPurchaseAttempt
	result = cls(Order=order, Processor=processor, Description=description,
				 State=state, StartTime=float(start_time))
	return result

def create_redeemed_purchase_attempt(purchase, redemption_code, redemption_time=None):

	redemption_time = redemption_time if redemption_time else time.time()

	# copy with order quantity none and item quantity to 1
	new_order = purchase.Order.copy()
	new_order.Quantity = None
	replace_quantity(new_order, 1)

	result = RedeemedPurchaseAttempt(
				Order=new_order, Processor=purchase.Processor,
				Description=purchase.Description, State=purchase.State,
				StartTime=purchase.StartTime, EndTime=purchase.EndTime,
				Error=purchase.Error, Synced=purchase.Synced,
				RedemptionTime=float(redemption_time),
				RedemptionCode=unicode(redemption_code))
	return result

def create_enrollment_attempt(order, processor=None, description=None, start_time=None):
	state = PA_STATE_SUCCESS
	start_time = start_time if start_time else time.time()
	result = EnrollmentPurchaseAttempt(Order=order, Processor=processor,
									   Description=description, State=state,
									   StartTime=float(start_time))
	return result
