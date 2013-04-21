# -*- coding: utf-8 -*-
""" Validators for numeric values.

Copyright (c) Karol Będkowski, 2006-2013

This file is part of wxGTD

This is free software; you can redistribute it and/or modify it under the
terms of the GNU General Public License as published by the Free Software
Foundation, version 2.
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2006-2013"
__version__ = '2013-04-21'

import gettext

from ._simple_validator import SimpleValidator

_ = gettext.gettext


##############################################################################


class MinValueValidator(SimpleValidator):
	""" Check if value is not less than configured.

	Args:
		min_value: minimal acceptable value
		error_message: optional error message
	"""

	def __init__(self, min_value, error_message=None):
		if error_message is None:
			error_message = _('Value too low (min=%d)') % min_value
		SimpleValidator.__init__(self, error_message)
		self._min = min_value

	def value_from_window(self, value):
		if value < self._min:
			self._raise_error()
		return value


##############################################################################


class MaxValueValidator(SimpleValidator):
	""" Validate if the value is not greater than configured.

	Args:
		max_value: maximal acceptable value
		error_message: optional error message
	"""
	def __init__(self, max_value, error_message=None):
		if error_message is None:
			error_message = _('Value too high (max=%d)') % max_value
		SimpleValidator.__init__(self, error_message)
		self._max = max_value

	def value_from_window(self, value):
		if value > self._max:
			self._raise_error()
		return value
