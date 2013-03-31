# -*- coding: utf-8 -*-
'''
validators/validators/time_validator.py

kpylibs 1.x
Copyright (c) Karol Będkowski, 2006-2013

This file is part of kpylibs

kpylibs is free software; you can redistribute it and/or modify it under the
terms of the GNU General Public License as published by the Free Software
Foundation, version 2.
'''

import re

import wx

from ._simple_validator import SimpleValidator
from .errors import ValidateError

_ = wx.GetTranslation
_RE_CHECK_TIME = re.compile(r'^(\d+):(\d\d)$')
_RE_CHECK_TIME_SEC = re.compile(r'^(\d+):(\d\d):(\d\d)$')


##############################################################################


class TimeValidator(SimpleValidator):
	''' Walidator czasu str -> wnd[str] -> str '''

	def __init__(self, show_sec=False, error_message=None):
		if error_message is None:
			if show_sec:
				error_message = _("Time isn't in correct format - "
						"HH:MM:SS format required")
			else:
				error_message = _("Time isn't in correct format - "
						"HH:MM format required")
		SimpleValidator.__init__(self, error_message)
		self._show_sec = show_sec

	def value_from_window(self, value):
		if value is None or value == '':
			return True
		try:
			m = re.match(_RE_CHECK_TIME_SEC if self._show_sec
					else _RE_CHECK_TIME, value)
			if int(m.group(2)) > 59:
				raise Exception()
			if self._show_sec and int(m.group(3)) > 59:
				raise Exception()
		except:
			raise ValidateError(self._error_message)
		return value


##############################################################################


class TimeToIntConv(SimpleValidator):
	''' Konwerter czasu int/long/str -> wnd [str] -> long '''

	def __init__(self, show_sec=False):
		SimpleValidator.__init__(self)
		self._show_sec = show_sec

	def value_from_window(self, value):
		if isinstance(value, (str, unicode)):
			result = 0
			for i in str(value).split(':'):
				result = result * 60 + int(i)
			return result
		return value

	def value_to_window(self, value):
		if isinstance(value, (str, unicode)):
			return value
		value = long(value or 0)
		if self._show_sec:
			s = value % 60
			m = value / 60 % 60
			h = value / 3600
			value = "%0d:%02d:%02d" % (h, m, s)
		else:
			m = value % 60
			h = value / 60
			value = "%02d:%02d" % (h, m)

		return value


##############################################################################


class DateValidator(SimpleValidator):
	''' walidator -> string/wxDateTime -> wnd[str/wxDateTime] -> wxDateTime '''

	def __init__(self, error_message=None):
		if error_message is None:
			error_message = _("Date isn't in correct format - "
					"YYYY-MM-DD format required")

		SimpleValidator.__init__(self, error_message)

	def value_from_window(self, value):
		if value is None:
			return value
		if isinstance(value, wx.DateTime):
			if value.IsOk():
				return value
			else:
				raise Exception()
		try:
			if isinstance(value, (int, long)):
				value = wx.DateTime(value)
			elif isinstance(value, (str, unicode)):
				value = wx.DateTime()
				value.ParseDate(value)
		except:
			self._raise_error()
		return value

	def value_to_window(self, value):
		if isinstance(value, (int, long)):
			value = wx.DateTime(value)
		elif isinstance(value, (str, unicode)):
			date = wx.DateTime()
			if value is not None:
				date.ParseDate(value)
			value = date
		else:
			value = wx.DateTime()
		if not value.IsValid():
			value = wx.DateTime_Now()
		return value


##############################################################################


class DateToIsoConv(SimpleValidator):
	''' conwerter any -> wnd -> str/long '''

	def value_from_window(self, value):
		if isinstance(value, wx.DateTime):
			return value.FormatISODate()
		return value
