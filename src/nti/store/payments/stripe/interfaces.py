#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Stripe Payment interfaces

.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

# pylint: disable=inherit-non-class,expression-not-assigned

from zope import interface

from zope.container.interfaces import IContainer

from zope.container.constraints import contains

from nti.base.interfaces import ICreated

from nti.dataserver.interfaces import ICreatedTime
from nti.dataserver.interfaces import IUser

from nti.property.property import alias as _alias

from nti.schema.field import Bool
from nti.schema.field import HTTPURL
from nti.schema.field import Int
from nti.schema.field import Number
from nti.schema.field import Object
from nti.schema.field import Set
from nti.schema.field import Variant
from nti.schema.field import ValidTextLine

from nti.store.interfaces import IPriceable
from nti.store.interfaces import IPricedItem
from nti.store.interfaces import IPricingError
from nti.store.interfaces import IPurchaseItem
from nti.store.interfaces import IPurchaseError
from nti.store.interfaces import IPurchaseOrder
from nti.store.interfaces import IOperationError
from nti.store.interfaces import IPaymentProcessor

from nti.store.payments.interfaces import IConnectKey
from nti.store.payments.interfaces import RegisterPurchaseData
from nti.store.payments.interfaces import IRegisterPurchaseData

#: Annotation key for stripe customer (legacy) 
STRIPE_CUSTOMER_KEY = 'nti.store.payments.stripe.stripe_adapters._StripeCustomer'

#: Annotation key for stripe purchase attempt (legacy) 
STRIPE_PURCHASE_KEY = 'nti.store.payments.stripe.stripe_adapters._StripePurchaseAttempt'


# stripe marker interfaces


class IStripeCoupon(interface.Interface):
    """
    marker interface for a stripe coupon
    """


class IStripeException(interface.Interface):
    """
    marker interface for a stripe exception
    """


class IInvalidStripeCoupon(IStripeException):
    """
    marker interface for an invalid stripe exception
    """


class INoSuchStripeCoupon(IStripeException):
    """
    marker interface for an no such stripe exception
    """


class IStripeError(interface.Interface):
    """
    marker interface for a stripe errors
    """


class IStripeAPIError(IStripeError):
    """marker interface for a stripe api error"""


class IStripeAPIConnectionError(IStripeError):
    """
    marker interface for a stripe api connection error
    """


class IStripeCardError(IStripeError):
    """
    marker interface for a stripe card errors
    """


class IStripeInvalidRequestError(IStripeError):
    """
    marker interface for a stripe invalid request errors
    """


class IStripeAuthenticationError(IStripeError):
    """
    marker interface for a stripe authentication errors
    """

# event interfaces


class IStripeCustomerCreated(interface.Interface):
    user = Object(IUser, title=u"The user")
    customer_id = ValidTextLine(title=u"The stripe customer identifier")


@interface.implementer(IStripeCustomerCreated)
class StripeCustomerCreated(object):

    def __init__(self, user, customer_id):
        self.user = user
        self.customer_id = customer_id


class IStripeCustomerDeleted(IStripeCustomerCreated):
    pass


@interface.implementer(IStripeCustomerDeleted)
class StripeCustomerDeleted(StripeCustomerCreated):
    pass


class IRegisterStripeToken(IRegisterPurchaseData):
    token = ValidTextLine(title=u"The token identifier")


@interface.implementer(IRegisterStripeToken)
class RegisterStripeToken(RegisterPurchaseData):

    def __init__(self, purchase, token_id):
        super(RegisterStripeToken, self).__init__(purchase)
        self.token_id = token_id

    token = _alias('token_id')


class IRegisterStripeCharge(IRegisterPurchaseData):
    charge_id = ValidTextLine(title=u"The charge identifier")


@interface.implementer(IRegisterStripeCharge)
class RegisterStripeCharge(RegisterPurchaseData):

    def __init__(self, purchase, charge_id):
        super(RegisterStripeCharge, self).__init__(purchase)
        self.charge_id = charge_id


# object interfaces


class IStripeConnectKey(IConnectKey):
    Alias = ValidTextLine(title=u'Key name or alias', required=True)
    LiveMode = Bool(title=u"Live mode flag", required=False)

    PrivateKey = ValidTextLine(title=u"The private key", required=True)
    PrivateKey.setTaggedValue('_ext_excluded_out', True)

    RefreshToken = ValidTextLine(title=u"Refresh token", required=False)
    RefreshToken.setTaggedValue('_ext_excluded_out', True)

    PublicKey = ValidTextLine(title=u"The private key", required=False)
    StripeUserID = ValidTextLine(title=u"String user id", required=False)


class IPersistentStripeConnectKey(ICreated, ICreatedTime, IStripeConnectKey):
    """
    Persisted Stripe connection key, e.g. those created via the UI and
    not registered via zcml configuration.
    """
    TokenType = ValidTextLine(title=u"Token type returned from token request, e.g. 'bearer'", required=True)


class IStripeOperationError(IOperationError):
    HttpStatus = Int(title=u'HTTP Status', required=False)
    Param = ValidTextLine(title=u"Optional parameter", required=False)


class IStripePurchaseError(IPurchaseError, IStripeOperationError):
    pass


class IStripePricingError(IPricingError):
    pass


class IStripeToken(interface.Interface):
    Type = ValidTextLine(title=u"The token type name.", required=False)
    Value = Variant((ValidTextLine(title=u"The token value."),
                     Number(title=u"The token value.")), required=True)
    CardID = ValidTextLine(title=u"The card id.", required=False)


class IStripePurchaseAttempt(interface.Interface):
    ChargeID = ValidTextLine(title=u'Charge id', required=False)
    TokenID = ValidTextLine(title=u'Token id', required=False)


class IStripeCustomer(interface.Interface):
    CustomerID = ValidTextLine(title=u'customer id')
    Charges = Set(value_type=ValidTextLine(title=u'the charge id'),
                  title=u'customer stripe charges')


class IStripePaymentProcessor(IPaymentProcessor):

    def create_token(customer_id=None, number=None, exp_month=None, exp_year=None,
                     cvc=None, api_key=None, **kwargs):
        """
        Create a stripe token

        :param customer_id Stripe customer id
        :param number Credit card number
        :param exp_month Expiration month
        :param exp_year Expiration year
        :param cvc CVC number
        """

    def validate_coupon(coupon):
        """
        validate the specfied coupon
        """

    def apply_coupon(amount, coupon=None):
        """
        apply the specfied coupon to the specfied amount
        """

    def process_purchase(purchase_id, username, token, expected_amount=None):
        """
        Process a purchase attempt

        :token Credit Card token
        """

    def get_payment_charge(purchase_id, username=None):
        """
        return a payment charge object (or None) for the specified purchase
        """

    def refund_purchase(purchase, amount=None, refund_application_fee=None):
        """
        Refunds a purchase

        :purchase Transaction/Purchase iden or object
        """


class IStripePriceable(IPriceable):
    Coupon = ValidTextLine(title=u'the coupon', required=False)


class IStripePurchaseItem(IStripePriceable, IPurchaseItem):
    pass


class IStripePurchaseOrder(IPurchaseOrder):
    Coupon = ValidTextLine(title=u'the coupon', required=False)


class IStripePricedItem(IPricedItem):
    Coupon = Object(interface.Interface, title=u'the coupon', required=False)


class IStripeConnectKeyContainer(IContainer):
    """
    An object containing Stripe connect keys
    """

    def add_key(key):
        """
        Add key to the container
        """

    def remove_key(key):
        """
        Remove key (or key name) from container
        """


class IStripeConnectConfig(interface.Interface):
    StripeOauthEndpoint = HTTPURL(title=u"Stripe Authorization Endpoint",
                                  description=u"The Stripe url to which the user will be "
                                              u"redirected to begin the OAuth flow.")

    ClientId = ValidTextLine(title=u"Platform Client ID",
                             description=u"The client id of the platform requesting "
                                         u"authorization.")

    TokenEndpoint = HTTPURL(title=u"Stripe Token Endpoint",
                            description=u"The Stripe OAuth endpoint at which the user "
                                        u"authorizes our platform.")

    DeauthorizeEndpoint = HTTPURL(title=u"Stripe Deauthorize Endpoint",
                                  description=u"The Stripe endpoint at which the user "
                                              u"deauthorizes our platform.")

    CompletionRoutePrefix = ValidTextLine(title=u"Completion Route Prefix",
                                          description=u"The prefix for the route to which the user"
                                                      u" will be directed on authorization "
                                                      u"completion.")

    SecretKey = ValidTextLine(title=u"Platform Secret Key",
                              description=u"Secret key of the platform requesting authorization.")

    StripeOauthBase = HTTPURL(title=u"Stripe OAuth Base",
                              description=u"Base url of Stripe's initial OAuth endpoint.")
