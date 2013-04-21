# -*- coding: utf-8 -*-
""" Validate values using regular expressions.

Copyright (c) Karol Będkowski, 2006-2013

This file is part of wxGTD.

This is free software; you can redistribute it and/or modify it under the
terms of the GNU General Public License as published by the Free Software
Foundation, version 2.
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2006-2013"
__version__ = '2013-04-21'

import re
import gettext

from ._simple_validator import SimpleValidator
from .errors import ValidateError

_ = gettext.gettext


##############################################################################


class ReValidator(SimpleValidator):
	""" Validator using regular expression.

	Args:
		retext: regular expression in Python re standard
		flags: flags used to compile regular expression.
		error_message: optional error message
	"""
	def __init__(self, retext, flags=0, error_message=None):
		if error_message is None:
			error_message = _('Incorrect value')

		SimpleValidator.__init__(self, error_message)
		self._retext = retext
		self._flags = flags
		self._re = re.compile(retext, flags)

	def value_from_window(self, value):
		if self._re.match(value) is None:
			raise ValidateError(self._error_message)

		return value
