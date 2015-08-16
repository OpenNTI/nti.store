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

from zope.container.interfaces import IContained
from zope.container.interfaces import IContainer

from zope.interface.common.sequence import IMinimalSequence
from zope.interface.common.mapping import IEnumerableMapping
from zope.interface.interfaces import ObjectEvent, IObjectEvent

from dolmen.builtins import IIterable

from nti.contentfragments.schema import HTMLContentFragment

from nti.dataserver.interfaces import IUser
from nti.dataserver.users.interfaces import checkEmailAddress

from .schema import DateTime

from nti.schema.field import Int
from nti.schema.field import Bool
from nti.schema.field import Float
from nti.schema.field import Choice
from nti.schema.field import Number
from nti.schema.field import Object
from nti.schema.field import Datetime
from nti.schema.field import FrozenSet
from nti.schema.field import Timedelta
from nti.schema.field import ValidText
from nti.schema.field import ListOrTuple
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
PA_STATE_REDEEMED = u'Redeemed'

PA_STATES = (PA_STATE_UNKNOWN, PA_STATE_FAILED, PA_STATE_FAILURE, PA_STATE_PENDING,
			 PA_STATE_STARTED, PA_STATE_DISPUTED, PA_STATE_REFUNDED, PA_STATE_SUCCESS,
			 PA_STATE_CANCELED, PA_STATE_RESERVED, PA_STATE_REDEEMED)
PA_STATE_VOCABULARY = \
	vocabulary.SimpleVocabulary([vocabulary.SimpleTerm(_x) for _x in PA_STATES])

PAYMENT_PROCESSORS = ('stripe',)
PAYMENT_PROCESSORS_VOCABULARY = \
	vocabulary.SimpleVocabulary([vocabulary.SimpleTerm(_x) for _x in PAYMENT_PROCESSORS])

class IStore(interface.Interface):
	"""
	Marker interface for a NTI Store
	"""

class IItemBundle(interface.Interface):
	NTIID = ValidTextLine(title='Content bundle NTTID', required=True)
	Title = ValidTextLine(title='Content bundle title', required=False)
	Author = ValidTextLine(title='Content bundle author', required=False)
	Description = HTMLContentFragment(title='Content bundle description',
									  required=False, default='')
	Items = FrozenSet(value_type=ValidTextLine(title='The item identifier'),
					  title="Bundle items")
IContentBundle = IItemBundle #BWC

class IPurchasableVendorInfo(IEnumerableMapping):
	"""
	Arbitrary purchasable vendor-specific information

	This is simply a dictionary and this module does not define
	the structure of it. However, it is recommended that the top-level
	keys be the vendor names and within them be the actual vendor specific
	information.
	"""

class IPurchasable(IItemBundle):
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
	Giftable = Bool(title="Giftable flag", required=False, default=False)
	Redeemable = Bool(title="Redeemable flag", required=False, default=False)
	RedeemCutOffDate = DateTime(title="Redeem cutoff date", required=False)
	IsPurchasable = Bool(title="Can be purchased", required=True, default=True,readonly=True)
	PurchaseCutOffDate = DateTime(title="Purchase cutoff date", required=False)
	VendorInfo = Object(IPurchasableVendorInfo, title="vendor info", required=False)
	VendorInfo.setTaggedValue('_ext_excluded_out', True)

class IPurchasableChoiceBundle(IPurchasable):
	"""
	marker interface for a purchasable choice bundle.

	Buyers can buy/redeem one item from the Items list.
	"""

class IPurchasableCourse(IPurchasable):
	Name = ValidTextLine(title='Course Name', required=False)

	# overrides
	Amount = Float(title="Cost amount", required=False, min=0.0, default=0.0)
	Provider = ValidTextLine(title='Course provider', required=False)

	# Deprecated/Legacy fields
	Featured = Bool(title='Featured flag', required=False, default=False)

	Preview = Bool(title='Course preview flag', required=False)
	StartDate = ValidTextLine(title="Course start date", required=False)
	Department = ValidTextLine(title='Course Department', required=False)

	Signature = ValidText(title='Course/Professor Signature', required=False)
	Communities = FrozenSet(value_type=ValidTextLine(title='The community identifier'),
							title="Communities", required=False)

	Duration = Timedelta(title="The length of the course",
						 description="Currently optional, may be None",
						 required=False)

	EndDate = Datetime(title="The date on which the course ends",
					   required=False)

	# For purchaseables, we want to share this.
	VendorInfo = Object(IPurchasableVendorInfo, title="vendor info", required=False)
	VendorInfo.setTaggedValue('_ext_excluded_out', False)
ICourse = IPurchasableCourse # alias BWC

class IPurchasableCourseChoiceBundle(IPurchasableChoiceBundle, IPurchasableCourse):
	pass

class ICopier(interface.Interface):
	"""
	An adapter to an object that is being copied
	"""

	def __call__(source, *args, **kwargs):
		"""
		Given the source object return a new copy.
		"""

class IPriceable(interface.Interface):
	NTIID = ValidTextLine(title='Purchasable item NTTID', required=True)
	Quantity = Int(title="Quantity", required=False, default=1, min=0)

	def copy():
		"""
		makes a new copy of this priceable
		"""

class IPurchaseItem(IPriceable):
	"""
	marker interface for a purchase order item
	"""

class IPurchaseOrder(IMinimalSequence):
	Items = ListOrTuple(value_type=Object(IPriceable), title='The items',
				  		required=True, min_length=1)

	Quantity = Int(title='Purchase bulk quantity (overwrites-item quantity)',
				   required=False)

	NTIIDs = interface.Attribute("Purchasable NTIIDs")
	NTIIDs.setTaggedValue('_ext_excluded_out', True)

	def copy(purchasables=None):
		"""
		makes a new copy of this purchase order

		:param purchasables Collection of purchasables to copy. None/Empty copy all
		"""

class IPricedItem(IPriceable):
	PurchaseFee = Float(title="Fee Amount", required=False)
	PurchaseFee.setTaggedValue('_ext_excluded_out', True)

	PurchasePrice = Float(title="Cost amount", required=True)
	NonDiscountedPrice = Float(title="Non discounted price", required=False)
	Currency = ValidTextLine(title='Currency ISO code', required=True, default='USD')

class IPricingResults(interface.Interface):
	Items = ListOrTuple(value_type=Object(IPricedItem), title='The priced items',
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

class IOperationError(interface.Interface):
	Type = ValidTextLine(title='Error type', required=True)
	Code = ValidTextLine(title='Error code', required=False)
	Message = ValidText(title='Error message', required=True)

class IPricingError(IOperationError):
	pass

class IPurchaseError(IOperationError):
	pass

class IRefundError(IOperationError):
	pass

class IRedemptionError(IOperationError):
	pass

class INTIStoreException(interface.Interface):
	"""
	interface for store exceptions
	"""

class IPurchaseException(INTIStoreException):
	"""
	interface for purchase exceptions
	"""

class IPricingException(INTIStoreException):
	"""
	interface for pricing exceptions
	"""

class IRefundException(INTIStoreException):
	"""
	interface for refund exceptions
	"""

class IRedemptionException(INTIStoreException):
	"""
	interface for redeeem exceptions
	"""

class IPurchasablePricer(interface.Interface):

	def price(priceable, registry=None):
		"""
		price the specfied priceable
		"""

	def evaluate(priceables, registry=None):
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

	def process_purchase(purchase, username, expected_amount=None):
		"""
		Process a purchase attempt

		:purchase purchase identifier
		:username User making the purchase
		:expected_amount: expected amount
		"""

	def refund_purchase(purchase, amount=None):
		"""
		Refund a purchase attempt

		:purchase purchase identifier
		:amount: expected amount
		"""

	def sync_purchase(purchase_id, username):
		"""
		Synchronized the purchase data with the payment processor info

		:purchase purchase identifier
		:user User that made the purchase
		"""

class IPurchaseAttemptContext(IEnumerableMapping):
	"""
	Arbitrary purchase attempt information

	This is simply a dictionary and this module does not define
	the structure of it.
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
	Error = Object(IOperationError, title='Error object', required=False)
	Synced = Bool(title='if the item has been synchronized with the processors data',
				  required=True, default=False)

	Context = Object(IPurchaseAttemptContext, title="Purchase attempt context",
					 required=False)
	Context.setTaggedValue('_ext_excluded_out', True)

	## CS. these fields are readonly and must not be created
	Items = interface.Attribute("Purchasable NTIIDs")
	Items.setTaggedValue('_ext_excluded_out', True)

	Profile = interface.Attribute('user profile')
	Profile.setTaggedValue('_ext_excluded_out', True)

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
	ExpirationTime = Number(title="The expirtation time", required=False)

	def isExpired(now=None):
		"""
		return if this invitation is expired
		"""

class IRedeemedPurchaseAttempt(IPurchaseAttempt):
	RedemptionTime = Number(title='Redemption time', required=True)
	RedemptionCode = ValidTextLine(title='Redemption Code', required=True)

class IGiftPurchaseAttempt(IPurchaseAttempt):
	Creator = ValidTextLine(title="Gift creator Email", required=True)
	SenderName = ValidTextLine(title='Sender name', required=False)
	Receiver = ValidTextLine(title='Receiver Email/username',
							 required=False,
							 constraint=checkEmailAddress)
	ReceiverName = ValidTextLine(title='Receiver name', required=False)
	Message = ValidText(title='Gift message', required=False)
	TargetPurchaseID = ValidTextLine(title='NTIID of target purchase', required=False)
	TargetPurchaseID.setTaggedValue('_ext_excluded_out', True)

	DeliveryDate = Datetime(title="The gift delivery date", required=False)

	Sender = interface.Attribute("Alias for Creator")
	Sender.setTaggedValue('_ext_excluded_out', True)

	From = interface.Attribute("alias for Creator")
	From.setTaggedValue('_ext_excluded_out', True)

	To = interface.Attribute("alias for Receiver Name")
	To.setTaggedValue('_ext_excluded_out', True)

	def is_redeemed():
		"""
		return if the purchase has been redeemed
		"""

class IPurchaseAttemptFactory(interface.Interface):
	"""
	Interface to create :class:`IPurchaseAttempt` objects.

	This factory are usually registered based the provider of the
	purchasable(s) being bought
	"""

	def create(order, processor, state=None, description=None, start_time=None,
			   context=None):

		"""
		:param order: a :class:`IPurchaseOrder` object.
		:param processor: A payment processor name
		:param description: Purchase attempt description'
		:param start_time: Purchase attempt start time
		:param start_time: a :class:`IPurchaseAttemptContext` object.
		"""

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
	charge = interface.Attribute('Purchase charge')
	request = interface.Attribute('Purchase pyramid request')

class IPurchaseAttemptDisputed(IPurchaseAttemptStateEvent):
	pass

class IPurchaseAttemptReserved(IPurchaseAttemptStateEvent):
	pass

class IPurchaseAttemptFailed(IPurchaseAttemptStateEvent):
	error = interface.Attribute('Failure error')

class IGiftPurchaseAttemptRedeemed(IPurchaseAttemptEvent):
	user = Object(IUser, title="The gift receiver")
	code = ValidTextLine(title="The gift code", required=False)
	request = interface.Attribute('Purchase request')

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

	def __init__(self, purchase, charge=None, request=None):
		super(PurchaseAttemptRefunded, self).__init__(purchase)
		self.charge = charge
		self.request = request

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

@interface.implementer(IGiftPurchaseAttemptRedeemed)
class GiftPurchaseAttemptRedeemed(PurchaseAttemptEvent):

	state = PA_STATE_REDEEMED

	def __init__(self, purchase, user, code=None, request=None):
		super(GiftPurchaseAttemptRedeemed, self).__init__(purchase)
		self.user = user
		self.code = code
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

	def get_pending_purchases():
		pass

	def clear():
		pass

	def values():
		"""
		Return all purchase attempts
		"""

class IStorePurchaseInvitation(interface.Interface):
	pass

# gift registry

class IUserGiftHistory(IContained):
	pass

class IGiftRegistry(IContainer, IContained):
	"""
	marker interface for gift registry.
	This object is registerd as a persistent utility
	"""

	def register_purchase(username, purchase):
		pass

	def get_pending_purchases(username, items=None):
		pass

# transformer

class IObjectTransformer(interface.Interface):
	"""
	Called to transform an object

	These are typically found as adapters, registered on the
	context object.

	The context object is passed to the ``__call__`` method to allow the adapter
	factories to return singleton objects such as a function.
	"""

	def __call__( context, user=None ):
		pass

# depreecated interfaces

deprecated('IEnrollmentAttempt', 'Use new course enrollment')
class IEnrollmentAttempt(IPurchaseAttempt):
	pass

deprecated('IEnrollmentPurchaseAttempt', 'Use new course enrollment')
class IEnrollmentPurchaseAttempt(IEnrollmentAttempt):
	Processor = ValidTextLine(title='Enrollment institution', required=False)
