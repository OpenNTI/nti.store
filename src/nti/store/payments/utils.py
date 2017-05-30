#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import re
import six

from zope import schema

from z3c.schema.payments import isValidCreditCard
from z3c.schema.payments import ISO7812CreditCard
from z3c.schema.payments import NotValidISO7812CreditCard


_cc = ISO7812CreditCard()


def is_valid_creditcard_number(s):
    """
    Returns True if the credit card number ``s`` is valid, False otherwise.
    """
    if isinstance(s, six.integer_types):
        s = str(s)
    elif isinstance(s, six.string_types):
        # Drop spaces and dashes, commonly entered by humans
        # Anything else we consider invalid
        s = s.replace(' ', '').replace('-', '')
    else:
        return False
    return _cc.constraint(s) and isValidCreditCard(s)


_digits_re = re.compile(r'^([0-9][0-9])')


def validate_credit_card(number, exp_month, exp_year, cvc=None):
    if not is_valid_creditcard_number(number):
        raise NotValidISO7812CreditCard(number)

    if not _digits_re.match(exp_month):
        raise schema.ValidationError('Invalid expiration month')

    if not _digits_re.match(exp_year):
        raise schema.ValidationError('Invalid expiration year')

    if cvc and not all([c.isdigit() for c in str(cvc)]):
        raise schema.ValidationError('Invalid CVC number')

    return True


AMEX_CC_RE = re.compile(r"^3[47][0-9]{13}$")
VISA_CC_RE = re.compile(r"^4[0-9]{12}(?:[0-9]{3})?$")
MASTERCARD_CC_RE = re.compile(r"^5[1-5][0-9]{14}$")
DISCOVER_CC_RE = re.compile(r"^6(?:011|5[0-9]{2})[0-9]{12}$")

CC_MAP = {"AMEX": AMEX_CC_RE, "VISA": VISA_CC_RE,
          "MASTERCARD": MASTERCARD_CC_RE, "DISCOVER": DISCOVER_CC_RE}


def credit_card_type(cc_number):
    """
    Function determines type of CC by the given number.

    http://code.activestate.com/recipes/577815-determine-credit-card-type-by-number/
    """
    for type_, regexp in CC_MAP.items():
        if regexp.match(str(cc_number)):
            return type_
    return None


def is_valid_credit_card_type(type_):
    type_ = type_.upper() if type else ''
    return type_ in CC_MAP
