#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import none
from hamcrest import is_not
from hamcrest import assert_that

import uuid

from nti.dataserver.users.users import User

from nti.store.payments.payeezy import PAYEEZY

from nti.store.purchase_history import register_purchase_attempt

from nti.store.purchase_order import PurchaseItem
from nti.store.purchase_order import create_purchase_order

from nti.store.purchase_attempt import create_purchase_attempt as purchase_attempt_creator

from nti.dataserver.tests import mock_dataserver


def create_user(username='nt@nti.com', password='temp001', **kwargs):
    ds = mock_dataserver.current_mock_ds
    ext_value = {'external_value': kwargs}
    usr = User.create_user(ds, username=username,
                           password=password, **ext_value)
    return usr


def create_purchase_attempt(item, quantity=None, description=None):
    item = PurchaseItem(NTIID=item, Quantity=1)
    order = create_purchase_order(item, quantity=quantity)
    result = purchase_attempt_creator(order, 
                                      processor=PAYEEZY,
                                      description=description or u'my charge')
    return result


def create_and_register_purchase_attempt(username, item, quantity=None, description=None):
    attempt = create_purchase_attempt(item, quantity=quantity, description=description)
    purchase_id = register_purchase_attempt(attempt, username)
    return purchase_id
