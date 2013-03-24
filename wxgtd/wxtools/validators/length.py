# -*- coding: utf-8 -*-
'''
validators/validators/length_validator.py

kpylibs 1.x
Copyright (c) Karol Będkowski, 2006-2013

This file is part of kpylibs

kpylibs is free software; you can redistribute it and/or modify it under the
terms of the GNU General Public License as published by the Free Software
Foundation, version 2.
'''

import wx

from ._simple_validator import SimpleValidator
from .errors import ValidateError

_ = wx.GetTranslation


##############################################################################

class NotEmptyValidator(SimpleValidator):
	def __init__(self, strip=False, error_message=None):
		if error_message is None:
			error_message = _('Field must by not empty')

		SimpleValidator.__init__(self, error_message)

		self._strip = strip

	def value_from_window(self, value):
		if value is None:
			raise ValidateError(self._error_message)

		if isinstance(value, str) or isinstance(value, unicode):
			value = value.strip() if self._strip else value
			if len(value) == 0:
				raise ValidateError(self._error_message)

		return value

#############################################################################


class MinLenValidator(SimpleValidator):
	def __init__(self, min_len, error_message=None):
		if error_message is None:
			error_message = _('Too few characters')

		SimpleValidator.__init__(self, error_message)
		self._min_len = min_len

	def value_from_window(self, value):
		value = str(value)
		if len(value) < self._min_len:
			raise ValidateError(self._error_message)

		return value

##############################################################################


class MaxLenValidator(SimpleValidator):
	def __init__(self, max_len, error_message=None):
		if error_message is None:
			error_message = _('Too many characters')

		SimpleValidator.__init__(self, error_message)
		self._max_len = max_len

	def value_from_window(self, value):
		value = str(value)
		if len(value) > self._max_len:
			raise ValidateError(self._error_message)

		return value
