# -*- coding: utf-8 -*-
'''
validators/validators/_simple_validator.py

kpylibs 1.x
Copyright (c) Karol Będkowski, 2006-2013

This file is part of kpylibs

kpylibs is free software; you can redistribute it and/or modify it under the
terms of the GNU General Public License as published by the Free Software
Foundation, version 2.
'''

from .errors import ValidateError


class SimpleValidator:
	def __init__(self, error_message=''):
		self._error_message = error_message

	@property
	def error(self):
		return self._error_message

	def value_from_window(self, value):
		''' simple_validator.value_from_window(value) -> value -- walidacja pola

			Jeżeli błąd - wyrzucany jest wyjątek ValidateError

			@param value - wartość pola do sprawdzenia
			@reeturn vartość pola (ewentualnie przetworzona)
		'''
		return value

	def value_to_window(self, value):
		return value

	def _raise_error(self, *args, **kwargs):
		raise ValidateError(self._error_message, *args, **kwargs)
