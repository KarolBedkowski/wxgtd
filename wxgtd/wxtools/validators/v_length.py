# -*- coding: utf-8 -*-
""" Simple validators for string values.

Copyright (c) Karol Będkowski, 2006-2013

This file is part of wxGTD.

This is free software; you can redistribute it and/or modify it under the
terms of the GNU General Public License as published by the Free Software
Foundation, version 2.
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2006-2013"
__version__ = '2013-04-21'

import gettext

from ._simple_validator import SimpleValidator
from .errors import ValidateError

_ = gettext.gettext


##############################################################################

class NotEmptyValidator(SimpleValidator):
	""" Check if the value is not empty or None.

	Also validator may strip white characters from string.

	Args:
		strip: if True strip white spaces from value.
		error_message: optional error message
	"""
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
	""" Check that the length of string is not too low.

	Args:
		min_len: minimal acceptable length of value
		error_message: optional error message
	"""
	def __init__(self, min_len, error_message=None):
		if error_message is None:
			error_message = _('Too few characters')

		SimpleValidator.__init__(self, error_message)
		self._min_len = min_len

	def value_from_window(self, value):
		value = str(value or '')
		if len(value) < self._min_len:
			raise ValidateError(self._error_message)
		return value

##############################################################################


class MaxLenValidator(SimpleValidator):
	""" Check if the string is not too long.

	Args:
		max_len: maximal acceptable length of value
		error_message: optional error message
	"""
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
