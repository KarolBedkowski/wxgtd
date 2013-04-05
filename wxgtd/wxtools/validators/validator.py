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
import gettext
import time

import wx
import wx.calendar
import wx.lib.masked

from .errors import ValidateError

_ = gettext.gettext


##############################################################################


class Validator(wx.PyValidator):
	def __init__(self, data_obj=None, data_key=None, validators=None,
				field=None, default=None, readonly=False):
		"""
			@param data_obj - obiekt z którego pobierane są dane
			@param data_key - klucz obiektu (atrybut, klucz itd)
			@param validators - [ SimpleValidator() ] - lista walidatorów
			@param field - nazwa pola (wyświetlana); jeżei brak - pobierana jest
					przez GetName() z widgeta
			@param default - domyślna wartość dla pola
			@param readonly - czy można zapisywać do obiektu

			Przykład:
			task = {}
			text_control.SetValidator(validators.Validator(task, 'title',
				validators=NotEmptyValidator(), field='title'))

			Uwagi:
				w dialogach:
					dlg.SetExtraStyle(wx.WS_EX_VALIDATE_RECURSIVELY)
				przy zapisie:
					if not dlg.Validate():
						return
					if not dlg.TransferDataFromWindow():
						return
		"""
		wx.PyValidator.__init__(self)
		self._object = data_obj
		self._key = data_key
		if isinstance(validators, (types.ListType, types.TupleType)) or \
				validators is None:
			self._validators = validators
		else:
			self._validators = [validators]
		self._field = field
		self._default = default
		self._readonly = readonly

	def Clone(self):
		"""	"""
		return self.__class__(self._object, self._key, self._validators,
				self._field, self._default, self._readonly)

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
							{'field': (self._field or control.GetName() or
									self._key or ''),
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
		if self._object:
			val = self._get_value()
			val = self._process_through_validators(val)
			self._set_value_to_control(val)
		return True

	def TransferFromWindow(self):
		if self._readonly:
			return True
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
		if self._object is not None:
			if hasattr(self._object, self._key):
				val = getattr(self._object, self._key)
			else:
				val = self._object.get(self._key)
		if val is None:
			val = self._default
		return val

	def _set_value(self, value):
		""" Ustawienie wartości w obiekcie """
		if self._object is not None:
			if hasattr(self._object, self._key):
				setattr(self._object, self._key, value)
			else:
				self._object[self._key] = value

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
		if isinstance(control, (wx.lib.masked.NumCtrl, wx.Slider)):
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


class ValidatorDate(Validator):
	""" Walidator dla wxDatePicker, wartości proste - timestamp"""

	def _set_value_to_control(self, value):
		ctrl = self.GetWindow()
		assert isinstance(ctrl, (wx.calendar.CalendarCtrl, wx.DatePickerCtrl)), \
				'Invalid control %r' % ctrl
		if value:
			date = wx.DateTime()
			date.SetTimeT(value)
			if isinstance(ctrl, wx.calendar.CalendarCtrl):
				ctrl.SetDate(date)
			else:
				ctrl.SetValue(date)

	def _get_value_from_control(self):
		ctrl = self.GetWindow()
		if isinstance(ctrl, wx.calendar.CalendarCtrl):
			datetime = ctrl.GetDate()
		else:
			datetime = ctrl.GetValue()
		if not datetime.IsValid():
			return None
		datetime.SetHour(0)
		datetime.SetMinute(0)
		datetime.SetSecond(0)
		return datetime.GetTicks()


class ValidatorTime(Validator):
	""" Walidator dla wxTextCtrl, który zawiera czas w formacie %X,
		wartości proste - timestamp"""

	def _set_value_to_control(self, value):
		ctrl = self.GetWindow()
		assert isinstance(ctrl, wx.TextCtrl), 'Invalid control %r' % ctrl
		ctrl.SetValue(time.strftime('%X', time.localtime(value)))

	def _get_value_from_control(self):
		ctrl = self.GetWindow()
		timestr = ctrl.GetValue()
		if timestr:
			value = time.strptime(timestr, '%X')
			return 3600 * value.tm_hour + 60 * value.tm_min + value.tm_sec
		return None
