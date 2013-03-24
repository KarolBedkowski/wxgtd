# -*- coding: utf-8 -*-
'''
validators/validators/regex_validator.py

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


##############################################################################


class ReValidator(SimpleValidator):
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
