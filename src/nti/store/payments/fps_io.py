# -*- coding: utf-8 -*-
"""
FDP IO operations

$Id: fps_io.py 15718 2013-02-08 03:30:41Z carlos.sanchez $
"""
from __future__ import print_function, unicode_literals, absolute_import
__docformat__ = "restructuredtext en"

import os
import hmac
import time
import uuid
import base64
import hashlib
import numbers
from datetime import date

from boto.exception import BotoServerError
from boto.fps.connection import FPSConnection

SINGLE_USE_PIPIELINE = 'SingleUse'
AWS_FPS_SANDBOX_HOST = 'fps.sandbox.amazonaws.com'

class FPSException(Exception):
	def __init__(self, error_message, reason=None, status=None):
		super(FPSException, self).__init__(error_message)
		self.reason = reason
		self.status = status

class FPSIO(object):
	
	def __init__(self):
		self._connection = None
		
	@property
	def connection(self):
		if self._connection is None:
			aws_host = os.getenv('AWS_FPS_HOST', AWS_FPS_SANDBOX_HOST)
			self._connection = FPSConnection(host=aws_host)
		return self._connection
	
	def signature(self, msg=None):
		msg = msg or str(uuid.uuid1())
		secret_access_key = self.connection.provider.secret_key
		dig = hmac.new(secret_access_key, msg=msg, digestmod=hashlib.sha256).digest()
		return base64.b64encode(dig).decode() 
	
	def _do_fps_operation(self,func, *args, **kwargs):
		try:
			result = func(*args, **kwargs)
			return result
		except BotoServerError, e:
			raise FPSException(e.error_message, e.reason, e.status)
		except Exception, e:
			raise FPSException(str(e))
		
	def get_cbui_url(self, caller_reference, return_url, amount, currency='USD', payment_reason=None, pipeline_name=None):
		"""
		Returns a [aws-fps] url to start a payment process
		
		:caller_reference:  buyer/caller/NTI transaction reference id
		:return_url: URL to return to after payment operation (submit/cancalation)
		"""
		payment_reason = payment_reason or ''
		pipeline_name = pipeline_name or SINGLE_USE_PIPIELINE
		inputs = {
				'transactionAmount':	amount,
				'currencyCode':		 	currency,
				'pipelineName':			pipeline_name,
				'returnURL':			return_url,
				'paymentReason':		payment_reason,
				'CallerReference':		caller_reference
		}
		url = self._do_fps_operation(self.connection.cbui_url, **inputs)
		return url

	def get_account_activity(self, start_date=None):
		"""
		Return the transactions starting from the specified date
		"""
		start_date = start_date or time.time()
		if isinstance(start_date, numbers.Real):
			d = date.fromtimestamp(start_date)
			start_date = d.strftime("%Y-%m-%d")
		result = self._do_fps_operation(self.connection.get_account_activity, StartDate=start_date)
		result = result.GetAccountActivityResult.Transaction # this the list of transactions
		return result
	
	def get_transaction(self, transaction_id):
		result = self._do_fps_operation(self.connection.get_transaction, TransactionId=transaction_id)
		result = result.GetTransactionResult.Transaction
		return result
	
	def get_account_balance(self):
		result = self._do_fps_operation(self.connection.get_account_balance)
		result = result.GetAccountBalanceResult.AccountBalance
		return result
	
	def get_token_by_caller(self, token):
		result = self._do_fps_operation(self.connection.get_token_by_caller, TokenId=token)
		result = result.GetTokenByCallerResult
		return result
	
	def pay(self, token, amount, currency='USD', reference=None):
		inputs = {
			'TransactionAmount.Value':			amount,
			'TransactionAmount.CurrencyCode':	currency,
			'SenderTokenId':					token,
			'CallerReference':					reference,
		}
		result = self.connection.pay(**inputs)
		return result
	
