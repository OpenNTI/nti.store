#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

from zope import interface
from zope.schema import vocabulary
from zope.deprecation import deprecated
from zope.interface.common import sequence
from zope.location.interfaces import IContained
from zope.interface.interfaces import ObjectEvent, IObjectEvent

from dolmen.builtins import IIterable

from nti.contentfragments.schema import HTMLContentFragment

from nti.schema.field import Int
from nti.schema.field import Bool
from nti.schema.field import List
from nti.schema.field import Float
from nti.schema.field import Tuple
from nti.schema.field import Choice
from nti.schema.field import Number
from nti.schema.field import Object
from nti.schema.field import Datetime
from nti.schema.field import FrozenSet
from nti.schema.field import Timedelta
from nti.schema.field import ValidText
from nti.schema.field import ValidTextLine

# : A :class:`zope.Interfaces.IVocabularyTokenized` vocabulary
# : will be available as a registered vocabulary under this name
PURCHASABLE_VOCAB_NAME = 'nti.store.purchasable.vocabulary'

PA_STATE_FAILED = u'Failed'
PA_STATE_SUCCESS = u'Success'
PA_STATE_FAILURE = u'Failure'
PA_STATE_PENDING = u'Pending'
PA_STATE_STARTED = u'Started'
PA_STATE_UNKNOWN = u'Unknown'
PA_STATE_DISPUTED = u'Disputed'
PA_STATE_REFUNDED = u'Refunded'
PA_STATE_CANCELED = u'Canceled'
PA_STATE_RESERVED = u'Reserved'

PA_STATES = (PA_STATE_UNKNOWN, PA_STATE_FAILED, PA_STATE_FAILURE, PA_STATE_PENDING,
			 PA_STATE_STARTED, PA_STATE_DISPUTED, PA_STATE_REFUNDED, PA_STATE_SUCCESS,
			 PA_STATE_CANCELED, PA_STATE_RESERVED)
PA_STATE_VOCABULARY = \
	vocabulary.SimpleVocabulary([vocabulary.SimpleTerm(_x) for _x in PA_STATES])

PAYMENT_PROCESSORS = ('stripe',)
PAYMENT_PROCESSORS_VOCABULARY = \
	vocabulary.SimpleVocabulary([vocabulary.SimpleTerm(_x) for _x in PAYMENT_PROCESSORS])

class IContentBundle(interface.Interface):
	NTIID = ValidTextLine(title='Content bundle NTTID', required=True)
	Title = ValidTextLine(title='Content bundle title', required=False)
	Author = ValidTextLine(title='Content bundle author', required=False)
	Description = HTMLContentFragment(title='Content bundle description',
									  required=False, default='')
	Items = FrozenSet(value_type=ValidTextLine(title='The item identifier'),
					  title="Bundle items")

class IPurchasable(IContentBundle):
	Amount = Float(title="Cost amount", required=True, min=0.0)
	Currency = ValidTextLine(title='Currency amount', required=True, default='USD')
	Discountable = Bool(title="Discountable flag", required=True, default=False)
	BulkPurchase = Bool(title="Bulk purchase flag", required=True, default=False)
	Fee = Float(title="Percentage fee", required=False, min=0.0)
	Icon = ValidTextLine(title='Icon URL', required=False)
	Thumbnail = ValidTextLine(title='Thumbnail URL', required=False)
	Provider = ValidTextLine(title='Purchasable item provider', required=True)
	License = ValidTextLine(title='Purchasable license', required=False)
	Public = Bool(title="Public flag", required=False, default=False)

deprecated('ICourse', 'Use new course specification')
class ICourse(IPurchasable):
	Name = ValidTextLine(title='Course Name', required=False)
	Featured = Bool(title='Featured flag', required=False, default=False)
	Preview = Bool(title='Course preview flag', required=False)
	StartDate = ValidTextLine(title="Course start date", required=False)
	Department = ValidTextLine(title='Course Department', required=False)
	Signature = ValidText(title='Course/Professor Signature', required=False)
	Communities = FrozenSet(value_type=ValidTextLine(title='The community identifier'),
							title="Communities")
	# overrides
	Amount = Float(title="Cost amount", required=False, min=0.0)
	Currency = ValidTextLine(title='Currency amount', required=False)
	Provider = ValidTextLine(title='Course provider', required=False)

	# Temporary BWC to match CourseCatalogEntry
	Duration = Timedelta(title="The length of the course",
						 description="Currently optional, may be None",
						 required=False)
	EndDate = Datetime(title="The date on which the course ends",
					   description="Currently optional; a missing value means the course has no defined end date.",
					   required=False)

class IPriceable(interface.Interface):
	NTIID = ValidTextLine(title='Purchasable item NTTID', required=True)
	Quantity = Int(title="Quantity", required=False, default=1, min=0)

	def copy():
		"""makes a new copy of this priceable"""

class IPurchaseItem(IPriceable):
	"""marker interface for a purchase order item"""

class IPurchaseOrder(sequence.IMinimalSequence):
	Items = Tuple(value_type=Object(IPriceable), title='The items',
				  required=True, min_length=1)

	Quantity = Int(title='Purchase bulk quantity (overwrites-item quantity)',
				   required=False)

	def copy():
		"""makes a new copy of this purchase order"""

class IPricedItem(IPriceable):
	PurchaseFee = Float(title="Fee Amount", required=False)
	PurchaseFee.setTaggedValue('_ext_excluded_out', True)
	
	PurchasePrice = Float(title="Cost amount", required=True)
	NonDiscountedPrice = Float(title="Non discounted price", required=False)
	Currency = ValidTextLine(title='Currency ISO code', required=True, default='USD')

class IPricingResults(interface.Interface):
	Items = List(value_type=Object(IPricedItem), title='The priced items',
				 required=True, min_length=0)
	
	TotalPurchaseFee = Float(title="Fee Amount", required=False)
	TotalPurchaseFee.setTaggedValue('_ext_excluded_out', True)
	
	TotalPurchasePrice = Float(title="Cost amount", required=True)
	TotalNonDiscountedPrice = Float(title="Non discounted price", required=False)
	Currency = ValidTextLine(title='Currency ISO code', required=True, default='USD')

class IUserAddress(interface.Interface):
	Street = ValidText(title='Street address', required=False)
	City = ValidTextLine(title='The city name', required=False)
	State = ValidTextLine(title='The state', required=False)
	Zip = ValidTextLine(title='The zip code', required=False, default=u'')
	Country = ValidTextLine(title='The country', required=False, default='USA')

class IPaymentCharge(interface.Interface):
	Amount = Float(title="Change amount", required=True)
	Created = Float(title="Created timestamp", required=True)
	Currency = ValidTextLine(title='Currency amount', required=True, default='USD')
	CardLast4 = Int(title='CreditCard last 4 digits', required=False)
	Name = ValidTextLine(title='The customer/charge name', required=False)
	Address = Object(IUserAddress, title='User address', required=False)

class IPurchaseError(interface.Interface):
	Type = ValidTextLine(title='Error type', required=True)
	Code = ValidTextLine(title='Error code', required=False)
	Message = ValidText(title='Error message', required=True)

class INTIStoreException(interface.Interface):
	""" marker interface for store exceptions """

class IPurchasablePricer(interface.Interface):

	def price(priceable):
		"""
		price the specfied priceable
		"""

	def evaluate(priceables):
		"""
		price the specfied priceables
		"""

class IPaymentProcessor(interface.Interface):

	name = ValidTextLine(title='Processor name', required=True)

	def validate_coupon(coupon):
		"""
		validate the specified coupon
		"""

	def apply_coupon(amount, coupon):
		"""
		apply the specified coupon to the specified amout
		"""

	def process_purchase(purchase_id, username, expected_amount=None):
		"""
		Process a purchase attempt

		:purchase_id purchase identifier
		:username User making the purchase
		:expected_amount: expected amount
		"""

	def refund_purchase(purchase_id):
		"""
		Refund a purchase attempt

		:purchase_id purchase identifier
		:username User making the purchase
		:expected_amount: expected amount
		"""

	def sync_purchase(purchase_id, username):
		"""
		Synchronized the purchase data with the payment processor info

		:purchase purchase identifier
		:user User that made the purchase
		"""

class IPurchaseAttempt(IContained):

	Processor = Choice(vocabulary=PAYMENT_PROCESSORS_VOCABULARY,
					   title='purchase processor', required=True)

	State = Choice(vocabulary=PA_STATE_VOCABULARY, title='Purchase state',
				   required=True)

	Order = Object(IPurchaseOrder, title="Purchase order", required=True)
	Description = ValidTextLine(title='A purchase description', required=False)

	StartTime = Number(title='Start time', required=True)
	EndTime = Number(title='Completion time', required=False)

	Pricing = Object(IPricingResults, title='Pricing results', required=False)
	Error = Object(IPurchaseError, title='Error object', required=False)
	Synced = Bool(title='if the item has been synchronized with the processors data',
				  required=True, default=False)

	def has_completed():
		"""
		return if the purchase has completed
		"""

	def has_failed():
		"""
		return if the purchase has failed
		"""

	def has_succeeded():
		"""
		return if the purchase has been successful
		"""

	def is_unknown():
		"""
		return if state of the purchase is unknown
		"""

	def is_pending():
		"""
		return if the purchase is pending (started)
		"""

	def is_refunded():
		"""
		return if the purchase has been refunded
		"""

	def is_disputed():
		"""
		return if the purchase has been disputed
		"""

	def is_reserved():
		"""
		return if the purchase has been reserved with the processor
		"""

	def is_canceled():
		"""
		return if the purchase has been canceled
		"""

	def is_synced():
		"""
		return if the purchase has been synchronized with the payment processor
		"""

class IInvitationPurchaseAttempt(IPurchaseAttempt):
	pass

class IEnrollmentAttempt(IPurchaseAttempt):
	pass

class IRedeemedPurchaseAttempt(IPurchaseAttempt):
	RedemptionTime = Number(title='Redemption time', required=True)
	RedemptionCode = ValidTextLine(title='Redemption Code', required=True)

class IEnrollmentPurchaseAttempt(IEnrollmentAttempt):
	Processor = ValidTextLine(title='Enrollment institution', required=False)

class IPurchaseAttemptEvent(IObjectEvent):
	object = Object(IPurchaseAttempt, title="The purchase")

class IPurchaseAttemptSynced(IPurchaseAttemptEvent):
	pass

class IPurchaseAttemptVoided(IPurchaseAttemptEvent):
	pass

class IPurchaseAttemptStateEvent(IPurchaseAttemptEvent):
	state = interface.Attribute('Purchase state')

class IPurchaseAttemptStarted(IPurchaseAttemptStateEvent):
	pass

class IPurchaseAttemptSuccessful(IPurchaseAttemptStateEvent):
	charge = interface.Attribute('Purchase charge')
	request = interface.Attribute('Purchase pyramid request')

class IPurchaseAttemptRefunded(IPurchaseAttemptStateEvent):
	pass

class IPurchaseAttemptDisputed(IPurchaseAttemptStateEvent):
	pass

class IPurchaseAttemptReserved(IPurchaseAttemptStateEvent):
	pass

class IPurchaseAttemptFailed(IPurchaseAttemptStateEvent):
	error = interface.Attribute('Failure error')


class IEnrollmentAttemptEvent(IPurchaseAttemptEvent):
	object = Object(IEnrollmentAttempt, title="The enrollment")

class IEnrollmentAttemptSuccessful(IEnrollmentAttemptEvent):
	request = interface.Attribute('Pyramid request')

class IUnenrollmentAttemptSuccessful(IEnrollmentAttemptEvent):
	request = interface.Attribute('Pyramid request')

@interface.implementer(IPurchaseAttemptEvent)
class PurchaseAttemptEvent(ObjectEvent):

	@property
	def purchase(self):
		return self.object

@interface.implementer(IPurchaseAttemptSynced)
class PurchaseAttemptSynced(PurchaseAttemptEvent):
	pass

@interface.implementer(IPurchaseAttemptVoided)
class PurchaseAttemptVoided(PurchaseAttemptEvent):
	pass

@interface.implementer(IPurchaseAttemptStarted)
class PurchaseAttemptStarted(PurchaseAttemptEvent):
	state = PA_STATE_STARTED

@interface.implementer(IPurchaseAttemptSuccessful)
class PurchaseAttemptSuccessful(PurchaseAttemptEvent):
	state = PA_STATE_SUCCESS
	def __init__(self, purchase, charge=None, request=None):
		super(PurchaseAttemptSuccessful, self).__init__(purchase)
		self.charge = charge
		self.request = request

@interface.implementer(IPurchaseAttemptRefunded)
class PurchaseAttemptRefunded(PurchaseAttemptEvent):
	state = PA_STATE_REFUNDED

@interface.implementer(IPurchaseAttemptDisputed)
class PurchaseAttemptDisputed(PurchaseAttemptEvent):
	state = PA_STATE_DISPUTED

@interface.implementer(IPurchaseAttemptReserved)
class PurchaseAttemptReserved(PurchaseAttemptEvent):
	state = PA_STATE_RESERVED

@interface.implementer(IPurchaseAttemptFailed)
class PurchaseAttemptFailed(PurchaseAttemptEvent):

	error = None
	state = PA_STATE_FAILED

	def __init__(self, purchase, error=None):
		super(PurchaseAttemptFailed, self).__init__(purchase)
		self.error = error

@interface.implementer(IEnrollmentAttemptEvent)
class EnrollmentAttemptEvent(PurchaseAttemptEvent):
	pass

@interface.implementer(IEnrollmentAttemptSuccessful)
class EnrollmentAttemptSuccessful(EnrollmentAttemptEvent):

	def __init__(self, purchase, request=None):
		super(EnrollmentAttemptSuccessful, self).__init__(purchase)
		self.request = request

@interface.implementer(IUnenrollmentAttemptSuccessful)
class UnenrollmentAttemptSuccessful(EnrollmentAttemptEvent):

	def __init__(self, purchase, request=None):
		super(UnenrollmentAttemptSuccessful, self).__init__(purchase)
		self.request = request

class IPurchaseHistory(IIterable):

	def add_purchase(purchase):
		pass

	def remove_purchase(purchase):
		pass

	def get_purchase(pid):
		pass

	def get_purchase_state(pid):
		pass

	def get_purchase_history(start_time=None, end_time=None):
		pass

	def values():
		"""
		Return all purchase attempts
		"""
class IStorePurchaseInvitation(interface.Interface):
	pass
