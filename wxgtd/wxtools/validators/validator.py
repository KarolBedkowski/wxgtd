# -*- coding: utf-8 -*-
# pylint: disable-msg=W0401, C0103
""" wxValidator wrapper.

Copyright (c) Karol Będkowski, 2006-2013

This file is part of wxGTD

This is free software; you can redistribute it and/or modify it under the
terms of the GNU General Public License as published by the Free Software
Foundation, version 2.
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2006-2013"
__version__ = "2013-04-21"

import types
import gettext
import time
import logging

import wx
import wx.calendar
import wx.lib.masked

from .errors import ValidateError

_LOG = logging.getLogger(__name__)
_ = gettext.gettext


##############################################################################


class Validator(wx.PyValidator):
	""" Validator for simple widgets.

	On TransferToWindow copy value from given object/key to widgets with
	conversion made by validators.

	On TransferDataFromWindow convert and validate value in control through
	validators. When any of validator raise exception, it show message box
	with appropriate message. Otherwise update object.

	Support widgets with GetValue/SetValue or GetDate/SetDate.

	Args:
		data_obj: object holding date
		data_key: name of attribute/key in data_obj for particular data
		validators: validator or list of validators (instances
			of SimpleValidator) used to validate convert and convert values.
		field: human name of control; if null - its read from widget
			by GetName()
		default: default value of field
		readonly: set value as read-only (bool)

	Example:
		task = {}
		text_control.SetValidator(Validator(task, 'title',
			validators=NotEmptyValidator(), field='title'))

	Remarks:
		In dialogs:
			dlg.SetExtraStyle(wx.WS_EX_VALIDATE_RECURSIVELY)
		Before close form:
			if not dlg.Validate():
				return
			if not dlg.TransferDataFromWindow():
				return
	"""
	def __init__(self, data_obj=None, data_key=None, validators=None,
				field=None, default=None, readonly=False):
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
		self._run_validation = True

	def enable(self, enabled=True):
		self._run_validation = enabled

	def Clone(self, *_args, **_kwars):
		"""	Clone validator.
		"""
		return self.__class__(self._object, self._key, self._validators,
				self._field, self._default, self._readonly)

	def Validate(self, win, *_args, **_kwars):
		""" Validate value in control.

		Args:
			win: widget

		Returns:
			True when value is ok.
		"""
		control = self.GetWindow()
		if self._run_validation and self._validators is not None:
			value = self._get_value_from_control()
			for validator in self._validators:
				try:
					value = validator.value_from_window(value)
				except ValidateError:
					# Error; show message box
					field_name = self._field or control.GetName() or self._key
					dlg = wx.MessageDialog(win,
							_('Validate field "%(field)s" failed:\n%(msg)s') %
							{'field': field_name or '', 'msg': validator.error},
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

	def TransferToWindow(self, *_args, **_kwars):
		""" Set value in control from configured object.

		Process value through all validators and set it in widget.
		Only, when object is configured.
		"""
		if self._object:
			val = self._get_value()
			val = self._process_through_validators(val)
			try:
				self._set_value_to_control(val)
			except:  # pylint: disable=W0702
				_LOG.exception("Validator.TransferToWindow error; value=%r",
						val)
		return True

	def TransferFromWindow(self, *_args, **_kwars):
		""" Get value from control, validate and convert and set it into object.
		"""
		if not self._readonly:
			value = self._get_value_from_control()
			if self._run_validation and self._validators is not None:
				for validator in self._validators:
					try:
						value = validator.value_from_window(value)
					except ValidateError:
						pass
			self._set_value(value)
		return True

	def _process_through_validators(self, value):
		""" Process value from objects by all validators.

		Value my be converted by any of validator.

		Args:
			value: value to convert (from object).
		"""
		if self._validators:
			for validator in reversed(self._validators):
				value = validator.value_to_window(value)
		return value

	def _get_value(self):
		""" Get value from object.

		Returns:
			Value
		"""
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
		""" Set value in object.

		Args:
			Value read from widgets, validated and converted.
		"""
		if self._object is not None and not self._readonly:
			if hasattr(self._object, self._key):
				setattr(self._object, self._key, value)
			else:
				self._object[self._key] = value

	def _get_value_from_control(self):
		""" Read value from control.

		Returns:
			Value.
		"""
		control = self.GetWindow()
		if isinstance(control, wx.calendar.CalendarCtrl):
			value = control.GetDate()
		else:
			value = control.GetValue()
		return value

	def _set_value_to_control(self, value):
		""" Set value from control.

		Args:
			value: value to set

		Raises:
			My raise various errors
		"""
		control = self.GetWindow()
		if isinstance(control, (wx.lib.masked.NumCtrl, wx.Slider, wx.SpinCtrl)):
			control.SetValue(value or 0)
		elif isinstance(control, (wx.CheckBox, wx.RadioButton)):
			control.SetValue(bool(value))
		elif isinstance(control, wx.calendar.CalendarCtrl):
			control.SetDate(value or '')
		else:
			control.SetValue(str(value or ''))


class ValidatorDv(Validator):
	""" Validator than can set/read values in controls which user select one
	option from list.

	Validator support controls: wxChoice, wxComboBox.
	Value in object is compared with ClientData or ClientObject.
	"""

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
		except:  # pylint: disable=W0702
			pass
		return value


class ValidatorColorStr(Validator):
	"""Validator for wxColorPickerCtrl that support colors defined as string.

	Color is defined as rgb definition in string:
		"#rrggbb"
		"rrggbb"
	with optional alpha channel:
		"#rrggbbaa"
		"rrggbbaa"

	Args:
		data_obj: object holding date
		data_key: name of attribute/key in data_obj for particular data
		validators: validator or list of validators (instances
			of SimpleValidator) used to validate convert and convert values.
		field: human name of control; if null - its read from widget
			by GetName()
		default: default value of field
		readonly: set value as read-only (bool)
		with_alpha: returned value will be contain information about alpha
			channel.
		add_hash: add hash (#) character on beginning of string
	"""
	def __init__(self, data_obj=None, data_key=None,  # pylint: disable=R0913
			validators=None, field=None, default=None, readonly=False,
			with_alpha=False, add_hash=False):
		Validator.__init__(self, data_obj, data_key, validators, field,
				default, readonly)
		self._with_alpha = with_alpha
		self._add_hash = add_hash

	def Clone(self):
		"""	Clone validator.
		"""
		return self.__class__(self._object, self._key, self._validators,
				self._field, self._default, self._readonly, self._with_alpha,
				self._add_hash)

	def _set_value_to_control(self, value):
		if value:
			if value[0] != "#":
				value = '#' + value
			color = wx.Color()
			color.SetFromString(value)
			self.GetWindow().SetColour(color)

	def _get_value_from_control(self):
		ctrl = self.GetWindow()
		color = ctrl.GetColour()
		value = color.GetAsString(wx.C2S_HTML_SYNTAX)
		if self._with_alpha:
			value += "%02X" % color.alpha
		if self._add_hash:
			if value[0] != '#':
				value = "#" + value
		else:
			if value[0] == '#':
				value = value[1:]
		return value


class ValidatorDate(Validator):
	""" Validator for wxDatePicker, time value as long (timestamp).
	"""

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
	""" Validator for wxTextCtrl containing time in %X format. Time as long
	(timestamp).
	"""

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
