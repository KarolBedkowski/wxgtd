# -*- coding: utf-8 -*-
""" Base class for validators.

Copyright (c) Karol Będkowski, 2006-2013

This file is part of wxGTD

This is free software; you can redistribute it and/or modify it under the
terms of the GNU General Public License as published by the Free Software
Foundation, version 2.
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2006-2013"
__version__ = '2013-04-21'

from .errors import ValidateError


class SimpleValidator:
	""" Base class for all validators.

	Attributes:
		error_message: message related to validation error.
	"""

	def __init__(self, error_message=''):
		self._error_message = error_message

	@property
	def error(self):
		""" Return error message for validator """
		return self._error_message

	def value_from_window(self, value):
		""" Validate and convert value read from widget.

		Args:
			value: value read from widget

		Returns:
			Converted and validated value

		Raises:
			ValidateError: An error occurred during validating value.
		"""
		return value

	def value_to_window(self, value):
		""" Convert value to widget.

		Convert value to appropriate format (i.e. date in string to wxDateTime).

		Args:
			value: original value

		Return:
			Converted value.
		"""
		return value

	def _raise_error(self, *args, **kwargs):
		""" Shortcut for raising validation error """
		raise ValidateError(self._error_message, *args, **kwargs)
