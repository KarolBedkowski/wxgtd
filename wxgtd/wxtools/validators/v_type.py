# -*- coding: utf-8 -*-
""" Validators for input type (number, float).

Copyright (c) Karol Będkowski, 2006-2013

This file is part of wxGTD.

This is free software; you can redistribute it and/or modify it under the
terms of the GNU General Public License as published by the Free Software
Foundation, version 2.
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2006-2013"
__version__ = '2013-04-21'

import locale
import gettext

from ._simple_validator import SimpleValidator
from .errors import ValidateError

_ = gettext.gettext


##############################################################################


class IntValidator(SimpleValidator):
	""" Check if value is number (int or long).

	Also convert value to long.

	Args:
		error_message: optional error message
	"""
	def __init__(self, error_message=None):
		if error_message is None:
			error_message = _('Integer value required')
		SimpleValidator.__init__(self, error_message)

	def value_from_window(self, value):
		if isinstance(value, int) or isinstance(value, long):
			return value
		try:
			value = locale.atoi(str(value))
		except:
			raise ValidateError(self._error_message)
		return value


##############################################################################


class FloatValidator(SimpleValidator):
	""" Check if value is float.

	Also convert value to float.

	Args:
		error_message: optional error message
	"""
	def __init__(self, error_message=None):
		if error_message is None:
			error_message = _('Float value required')
		SimpleValidator.__init__(self, error_message)

	def value_from_window(self, value):
		if isinstance(value, float):
			return value
		try:
			value = locale.atof(str(value))
		except:
			raise ValidateError(self._error_message)
		return value
