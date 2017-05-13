#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import none
from hamcrest import is_not
from hamcrest import assert_that

import uuid

from nti.dataserver.users import User

from nti.store.payments.stripe.stripe_purchase import create_stripe_purchase_item
from nti.store.payments.stripe.stripe_purchase import create_stripe_purchase_order

from nti.store.purchase_attempt import create_purchase_attempt as purchase_attempt_creator

from nti.store.purchase_history import register_purchase_attempt

import nti.dataserver.tests.mock_dataserver as mock_dataserver


def create_user(username=u'nt@nti.com', password=u'temp001', **kwargs):
    ds = mock_dataserver.current_mock_ds
    ext_value = {'external_value': kwargs}
    usr = User.create_user(ds, username=username,
                           password=password, **ext_value)
    return usr


def create_random_user():
    code = str(uuid.uuid4()).split('-')[0]
    username = u'u' + code
    email = username + u'@nextthought.com'
    desc = u'test user ' + code
    user = create_user(username=username, email=email, description=desc)
    return user


def create_purchase_attempt(item, processor, quantity=None, 
                            description=None, coupon=None):
    item = create_stripe_purchase_item(item, 1)
    order = create_stripe_purchase_order(item, 
                                         quantity=quantity, 
                                         coupon=coupon)
    result = purchase_attempt_creator(order,
                                      processor=processor,
                                      description=description)
    return result


def create_and_register_purchase_attempt(username, item, quantity=None,
                                         processor=None,coupon=None, 
                                         description=u"my charge"):
    pa = create_purchase_attempt(item, quantity=quantity, processor=processor,
                                 coupon=coupon, description=description)
    purchase_id = register_purchase_attempt(pa, username)
    return purchase_id


def create_purchase(self, item=None, amount=100, coupon=None, manager=None,
                    quantity=None, username=None):
    ds = self.ds
    manager = manager or self.manager
    item = item or self.book_id

    with mock_dataserver.mock_db_trans(ds):
        if username is None:
            user = create_random_user()
        else:
            user = create_user(username=username, email=username)
        username = user.username

    with mock_dataserver.mock_db_trans(ds):
        purchase_id = create_and_register_purchase_attempt(username, item=item,
                                                           processor=manager.name,
                                                           coupon=coupon,
                                                           quantity=quantity)
        assert_that(purchase_id, is_not(none()))

    tid = manager.create_card_token(number=u"5105105105105100",
                                    exp_month=u"11",
                                    exp_year=u"30",
                                    cvc=u"542",
                                    address=u"3001 Oak Tree #D16",
                                    city=u"Norman",
                                    zip=u"73072",
                                    state=u"OK",
                                    country=u"USA")

    cid = manager.process_purchase(token=tid,
                                   username=username,
                                   purchase_id=purchase_id,
                                   expected_amount=amount)

    assert_that(tid, is_not(none()))
    assert_that(cid, is_not(none()))

    return username, purchase_id, tid, cid
