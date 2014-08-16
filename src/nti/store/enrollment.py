#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Enrollment functionality

.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import zope.deprecation
zope.deprecation.deprecated("nti.store.enrollment", "no longer for course enrolling")

from zope import component
from zope.event import notify

from .course import get_course

from .purchase_order import create_purchase_item
from .purchase_order import create_purchase_order

from .purchase_history import remove_purchase_attempt
from .purchase_history import register_purchase_attempt
from .purchase_history import get_purchase_history_by_item


from nti.deprecated import hiding_warnings
with hiding_warnings():
	from .purchase_attempt import create_enrollment_attempt
	from .interfaces import IEnrollmentPurchaseAttempt
	from .interfaces import EnrollmentAttemptSuccessful
	from .interfaces import UnenrollmentAttemptSuccessful

class CourseNotFoundException(Exception):
	pass

class UserNotEnrolledException(Exception):
	pass

class InvalidEnrollmentAttemptException(Exception):
	pass

def get_enrollment(user, course_id):
	history = get_purchase_history_by_item(user, course_id)
	for enrollment in history or ():
		if IEnrollmentPurchaseAttempt.providedBy(enrollment):
			return enrollment
	return None

def is_enrolled(user, course_id):
	enrollment = get_enrollment(user, course_id)
	return enrollment is not None

def do_enrollment(user, course_id, description=None, request=None, registry=component):
	item = create_purchase_item(course_id, 1)
	order = create_purchase_order(item, quantity=1)
	purchase = create_enrollment_attempt(order, description=description)
	if not is_enrolled(user, course_id):
		register_purchase_attempt(purchase, user)
		notify(EnrollmentAttemptSuccessful(purchase, request))
		return True
	return False

def enroll_course(user, course_id, description=None, request=None, registry=component):
	if get_course(course_id, registry=registry) is None:
		raise CourseNotFoundException()
	return do_enrollment(user, course_id, description, request, registry=registry)

def unenroll_course(user, course_id, request=None, registry=component):
	if get_course(course_id, registry=registry) is None:
		raise CourseNotFoundException()

	enrollment = get_enrollment(user, course_id)
	if enrollment is None:
		logger.debug("user %s is not enrolled in course %s" % (user, course_id))
		raise UserNotEnrolledException()

	purchase = enrollment
	assert IEnrollmentPurchaseAttempt.providedBy(purchase)

	remove_purchase_attempt(purchase, user)
	notify(UnenrollmentAttemptSuccessful(purchase, request=request))
	return True
