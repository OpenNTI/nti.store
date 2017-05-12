#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

from zope import interface

from nti.schema.field import Object
from nti.schema.field import TextLine as ValidTextLine

from nti.store.interfaces import IPriceable
from nti.store.interfaces import IPurchaseAttempt


class IConnectKey(interface.Interface):
    Provider = ValidTextLine(title=u'Key name or alias', required=True)


class ICouponPriceable(IPriceable):
    Coupon = ValidTextLine(title=u"The coupon", required=False)


class IRegisterPurchaseData(interface.Interface):
    object = Object(IPurchaseAttempt, title=u"The purchase", required=True)


class RegisterPurchaseData(object):

    def __init__(self, obj):
        self.object = obj

    @property
    def purchase(self):
        return self.object
