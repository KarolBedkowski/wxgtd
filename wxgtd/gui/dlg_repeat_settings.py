# -*- coding: utf-8 -*-
""" Repeat task settings dialog,

Copyright (c) Karol Będkowski, 2013

This file is part of wxGTD
Licence: GPLv2+
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2013"
__version__ = "2013-04-28"

import logging
import gettext

import wx

from wxgtd.model import enums
from wxgtd.model import logic

from ._base_dialog import BaseDialog

_LOG = logging.getLogger(__name__)
_ = gettext.gettext


class DlgRepeatSettings(BaseDialog):
	""" Repeat task settings dialog.

	Args:
		parent: parent windows
		pattern: repeat pattern (enums.REMIND_PATTERNS)
		repeat_from: true = repeat for complete; false = from due.
	"""

	def __init__(self, parent, pattern, repeat_from):
		self._data = {'pattern': pattern, 'from': repeat_from}
		BaseDialog.__init__(self, parent, 'dlg_repeat_settings', save_pos=False)
		self._setup_comboboxes()
		self._setup(pattern, repeat_from)

	@property
	def repeat_from(self):
		return self._data['from']

	@property
	def pattern(self):
		return self._data['pattern']

	def _create_bindings(self, wnd):
		BaseDialog._create_bindings(self, wnd)
		self['c_every'].Bind(wx.EVT_CHOICE, self._on_cb_every_pattern)
		self['sc_everyxt_num'].Bind(wx.EVT_SPINCTRL, self._on_every_xt_sc)
		self['c_everyxt_period'].Bind(wx.EVT_CHOICE, self._on_every_xt_period)
		self['cb_mon'].Bind(wx.EVT_CHECKBOX, self._on_every_w_day)
		self['cb_tue'].Bind(wx.EVT_CHECKBOX, self._on_every_w_day)
		self['cb_wed'].Bind(wx.EVT_CHECKBOX, self._on_every_w_day)
		self['cb_thu'].Bind(wx.EVT_CHECKBOX, self._on_every_w_day)
		self['cb_fri'].Bind(wx.EVT_CHECKBOX, self._on_every_w_day)
		self['cb_sat'].Bind(wx.EVT_CHECKBOX, self._on_every_w_day)
		self['cb_sun'].Bind(wx.EVT_CHECKBOX, self._on_every_w_day)
		self['cb_xdm_num_wday'].Bind(wx.EVT_CHOICE, self._on_xdm_num_wdays)
		self['c_xdm_weekday'].Bind(wx.EVT_CHOICE, self._on_xdm_weekday)
		self['sc_xdm_months'].Bind(wx.EVT_SPINCTRL, self._on_xdm_months)

	def _setup(self, pattern, repeat_from):
		_LOG.debug("DlgRemindSettings(%r)", (pattern, repeat_from))
		self['rb_never'].SetValue(True)
		self['rb_completion'].SetValue(bool(repeat_from))

		if pattern:
			if _choice_select_by_data(self['c_every'], pattern):
				self['rb_every'].SetValue(True)
				return
			m_repeat_xt = logic.RE_REPEAT_XT.match(pattern)
			if m_repeat_xt:
				self['sc_everyxt_num'].SetValue(int(m_repeat_xt.group(1)))
				period = m_repeat_xt.group(2)
				period = {'Weeks': 'Week', 'Days': 'Day', 'Months': 'Month',
						'Years': 'Year'}.get(period, period)
				if _choice_select_by_data(self['c_everyxt_period'], period):
					self['rb_everyxt'].SetValue(True)
					return
			if logic.RE_REPEAT_EVERYW.match(pattern):
				pattern = pattern.lower()
				self['cb_mon'].SetValue('mon' in pattern)
				self['cb_thu'].SetValue('thu' in pattern)
				self['cb_wed'].SetValue('wed' in pattern)
				self['cb_tue'].SetValue('tue' in pattern)
				self['cb_fri'].SetValue('fri' in pattern)
				self['cb_sat'].SetValue('sat' in pattern)
				self['cb_sun'].SetValue('sun' in pattern)
				self['rb_everyw'].SetValue(True)
				return
			if pattern.startswith("The ") and pattern.endswith(' months'):
				_foo, num_wday, wday, _foo, num_month, _foo = pattern.split(' ')
				self['sc_xdm_months'].SetValue(int(num_month))
				_choice_select_by_data(self['c_xdm_weekday'], wday)
				_choice_select_by_data(self['cb_xdm_num_wday'], num_wday)
				self['rb_xdm'].SetValue(True)
				return
			# brak znanego typu
			_LOG.warn("DlgRepeatSettings.setup: wrong pattern: %r", pattern)

	def _setup_comboboxes(self):
		c_every = self['c_every']
		for rem_key, rem_name in enums.REPEAT_PATTERN_LIST:
			c_every.Append(rem_name, rem_key)
		c_every.Select(0)
		c_everyxt_period = self['c_everyxt_period']
		c_everyxt_period.Append(_("days"), "Day")
		c_everyxt_period.Append(_("weeks"), "Week")
		c_everyxt_period.Append(_("months"), "Month")
		c_everyxt_period.Append(_("years"), "Year")
		c_everyxt_period.Select(0)
		cb_xdm_num_wday = self['cb_xdm_num_wday']
		cb_xdm_num_wday.Append(_("first"), 'first')
		cb_xdm_num_wday.Append(_("second"), 'second')
		cb_xdm_num_wday.Append(_("third"), 'third')
		cb_xdm_num_wday.Append(_("fourth"), 'fourth')
		cb_xdm_num_wday.Append(_("fifth"), 'fifth')
		cb_xdm_num_wday.Append(_("last"), 'last')
		cb_xdm_num_wday.Select(0)
		c_xdm_weekday = self['c_xdm_weekday']
		c_xdm_weekday.Append(_("Monday"), "Mon")
		c_xdm_weekday.Append(_("Tuesday"), "Tue")
		c_xdm_weekday.Append(_("Wednesday"), "Wed")
		c_xdm_weekday.Append(_("Thursday"), "Thu")
		c_xdm_weekday.Append(_("Friday"), "Fri")
		c_xdm_weekday.Append(_("Saturday"), "Sat")
		c_xdm_weekday.Append(_("Sunday"), "Sun")
		c_xdm_weekday.Select(0)

	def _on_ok(self, evt):
		self._data['from'] = 1 if self['rb_completion'].GetValue() else 0
		if self['rb_never'].GetValue():
			self._data['pattern'] = None
		elif self['rb_everyxt'].GetValue():
			pattern = logic.build_repeat_pattern_every_xt(
					self['sc_everyxt_num'].GetValue(),
					_get_choice_selected(self['c_everyxt_period']))
			self._data['pattern'] = pattern
		elif self['rb_everyw'].GetValue():
			pattern = logic.build_repeat_pattern_every_w(
					self['cb_mon'].GetValue(),
					self['cb_tue'].GetValue(),
					self['cb_wed'].GetValue(),
					self['cb_thu'].GetValue(),
					self['cb_fri'].GetValue(),
					self['cb_sat'].GetValue(),
					self['cb_sun'].GetValue())
			self._data['pattern'] = pattern
		elif self['rb_xdm'].GetValue():
			pattern = logic.build_repeat_pattern_every_xdm(
					_get_choice_selected(self['cb_xdm_num_wday']),
					_get_choice_selected(self['c_xdm_weekday']),
					self['sc_xdm_months'].GetValue())
			self._data['pattern'] = pattern
		else:
			self._data['pattern'] = _get_choice_selected(self['c_every'])
		BaseDialog._on_ok(self, evt)

	def _on_cb_every_pattern(self, _evt):
		if self._wnd.IsActive():
			self['rb_every'].SetValue(True)

	def _on_every_xt_sc(self, _evt):
		if self._wnd.IsActive():
			self['rb_everyxt'].SetValue(True)

	def _on_every_xt_period(self, _evt):
		if self._wnd.IsActive():
			self['rb_everyxt'].SetValue(True)

	def _on_every_w_day(self, _evt):
		if self._wnd.IsActive():
			self['rb_everyw'].SetValue(True)

	def _on_xdm_num_wdays(self, _evt):
		if self._wnd.IsActive():
			self['rb_xdm'].SetValue(True)

	def _on_xdm_weekday(self, _evt):
		if self._wnd.IsActive():
			self['rb_xdm'].SetValue(True)

	def _on_xdm_months(self, _evt):
		if self._wnd.IsActive():
			self['rb_xdm'].SetValue(True)


def _choice_select_by_data(control, value):
	for idx in xrange(control.GetCount()):
		if control.GetClientData(idx) == value:
			control.Select(idx)
			return True
	_LOG.warn('_choice_select_by_data value=%r not found', value)
	return False


def _get_choice_selected(control):
	return control.GetClientData(control.GetSelection())
