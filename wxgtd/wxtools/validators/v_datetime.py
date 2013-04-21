# -*- coding: utf-8 -*-
""" Validators for time and date.

Copyright (c) Karol Będkowski, 2006-2013

This file is part of wxGTD

This is free software; you can redistribute it and/or modify it under the
terms of the GNU General Public License as published by the Free Software
Foundation, version 2.
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2006-2013"
__version__ = '2013-04-21'

import re
import gettext

import wx

from ._simple_validator import SimpleValidator
from .errors import ValidateError

_ = gettext.gettext

_RE_CHECK_TIME = re.compile(r'^(\d+):(\d\d)$')
_RE_CHECK_TIME_SEC = re.compile(r'^(\d+):(\d\d):(\d\d)$')


##############################################################################


class TimeValidator(SimpleValidator):
	""" Validate if the string is time formated as HH:MM[:SS].

	Args:
		show_sec: if True, validate using format HH:MM:SS
		error_message: optional error message
	"""
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
		match = re.match(_RE_CHECK_TIME_SEC if self._show_sec
				else _RE_CHECK_TIME, value)
		if (not match or int(match.group(2)) > 59 or
				(self._show_sec and int(match.group(3)) > 59)):
			raise ValidateError(self._error_message)
		return value


##############################################################################


class TimeToIntConv(SimpleValidator):
	""" Convert time as timestamp (number) to string for use in textctrl.

	Validator convert timestamp to string "HH:DD[:SS]" for display in widget,
	and from string to number for store in object.

	Args:
		show_sec: if True using format HH:MM:SS
	"""
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
			sec = value % 60
			minutes = value / 60 % 60
			hours = value / 3600
			value = "%0d:%02d:%02d" % (hours, minutes, sec)
		else:
			minutes = value % 60
			hours = value / 60
			value = "%02d:%02d" % (hours, minutes)
		return value


##############################################################################


class DateValidator(SimpleValidator):
	""" Convert date value (as string or wx.DateTime to use in control.

	Validator convert given value (long/string) to wx.DateTime for show in
	control, and back to wx.DateTime when storing in object.
	Date as string must be in format acceptable by wx.DateTime.

	Args:
		error_message: optional error message.
	"""
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
	""" Convert date as wx.DateTime to string in ISO format. """

	def value_from_window(self, value):
		if isinstance(value, wx.DateTime):
			return value.FormatISODate()
		return value
