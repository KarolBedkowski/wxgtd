# -*- coding: utf-8 -*-
# pylint: disable-msg=W0401, C0103
'''
validators/my_validator.py

kpylibs 1.x
Copyright (c) Karol Będkowski, 2006-2013

This file is part of kpylibs

kpylibs is free software; you can redistribute it and/or modify it under the
terms of the GNU General Public License as published by the Free Software
Foundation, version 2.
'''

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2006-2013"
__version__ = "2013-02-17"
__all__ = ['Validator', 'ValidatorDv']


import types

import wx
import wx.calendar
import wx.lib.masked

from .errors import ValidateError

_ = wx.GetTranslation


##############################################################################


class Validator(wx.PyValidator):
	def __init__(self, data_key=None, validators=None, field=None, default=None):
		"""
			@param data_key = (dict(), key) | (obiekt, attribute_name)
			@param validators = [ SimpleValidator() ]
			@param field = field name
			@param default =  domyślna wartość dla pola
		"""
		wx.PyValidator.__init__(self)
		self._data = data_key
		if isinstance(validators, (types.ListType, types.TupleType)) or \
				validators is None:
			self._validators = validators
		else:
			self._validators = [validators]
		self._field = field
		self._default = default

	def Clone(self):
		"""	"""
		return self.__class__(self._data, self._validators, self._field)

	def Validate(self, win):
		""" Validacja pola """
		control = self.GetWindow()

		if self._validators is not None:
			value = self._get_value_from_control()
			for validator in self._validators:
				try:
					value = validator.value_from_window(value)
				except ValidateError:
					dlg = wx.MessageDialog(win,
							_('Validate field "%(field)s" failed:\n%(msg)s') %
							{'field': (self._field or self._data[1] or ''),
									'msg': validator.error},
							_('Validate error'),
							wx.OK | wx.CENTRE | wx.ICON_ERROR)
					dlg.ShowModal()
					dlg.Destroy()
					control.SetBackgroundColour('red')
					control.SetFocus()
					control.Refresh()
					return False

		control.SetBackgroundColour(wx.SystemSettings_GetColour(
				wx.SYS_COLOUR_WINDOW))
		control.Refresh()
		return True

	def TransferToWindow(self):
		if self._data:
			val = self._get_value()
			val = self._process_through_validators(val)
			self._set_value_to_control(val)
		return True

	def TransferFromWindow(self):
		value = self._get_value_from_control()
		if self._validators is not None:
			for validator in self._validators:
				value = validator.value_from_window(value)
		self._set_value(value)
		return True

	def _process_through_validators(self, value):
		"""
		Przeprocesowanie wartści przez wszystkie validatory.
		"""
		if self._validators:
			validators = self._validators[:]
			validators.reverse()
			for validator in validators:
				value = validator.value_to_window(value)
		return value

	def _get_value(self):
		""" Pobranie aktualnej wartości z obiektu """
		val = None
		if self._data is not None:
			data, key = self._data
			if hasattr(data, key):
				val = getattr(data, key)
			else:
				val = data.get(key)
		if val is None:
			val = self._default
		return val

	def _set_value(self, value):
		""" Ustawienie wartości w obiekcie """
		if self._data is not None:
			data, key = self._data
			if hasattr(data, key):
				setattr(data, key, value)
			else:
				data[key] = value

	def _get_value_from_control(self):
		""" Pobranie wartości z widgetu """
		control = self.GetWindow()
		if isinstance(control, wx.calendar.CalendarCtrl):
			value = control.GetDate()
		else:
			value = control.GetValue()
		return value

	def _set_value_to_control(self, value):
		""" Ustawienei wartości w widgecie """
		control = self.GetWindow()
		if isinstance(control, wx.lib.masked.NumCtrl):
			control.SetValue(value or 0)
		elif isinstance(control, (wx.CheckBox, wx.RadioButton)):
			control.SetValue(bool(value))
		elif isinstance(control, wx.calendar.CalendarCtrl):
			control.SetDate(value or '')
		else:
			control.SetValue(str(value or ''))


class ValidatorDv(Validator):
	""" Walidator dla elementów, które się wybieralne a wartość jest ustawiona
	jako w ClientData"""

	def _set_value_to_control(self, value):
		ctrl = self.GetWindow()
		for i in xrange(ctrl.GetCount()):
			print self._data[1], ctrl.GetClientData(i), value
			if ctrl.GetClientData(i) == value:
				ctrl.Select(i)
				return
		if hasattr(ctrl, 'GetClientObject'):
			for i in xrange(ctrl.GetCount()):
				if ctrl.GetClientObject(i) == value:
					ctrl.Select(i)
					return

	def _get_value_from_control(self):
		value = None
		ctrl = self.GetWindow()
		try:
			value = ctrl.GetClientData(ctrl.GetSelection())
		except:
			pass
		return value
