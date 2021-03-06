# -*- coding: utf-8 -*-
""" Remind setting dialog.

Copyright (c) Karol Będkowski, 2013

This file is part of wxGTD
Licence: GPLv2+
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2013"
__version__ = "2013-04-28"

import logging

import wx

from wxgtd.wxtools.validators import ValidatorDate, ValidatorTime
from wxgtd.model import enums

from ._base_dialog import BaseDialog

_LOG = logging.getLogger(__name__)


class DlgRemindSettings(BaseDialog):
	""" Remind setting dialog.

	Args:
		parent: parent window
		alarm: current alarm (date, time)
		alarm_pattern: alarm pattern used to set alarm dynamically.
		no_date: don't allow set exact date
	"""

	def __init__(self, parent, alarm, alarm_pattern, no_date=False):
		BaseDialog.__init__(self, parent, 'dlg_remind_settings', save_pos=False)
		self._setup(alarm, alarm_pattern, no_date)

	@property
	def alarm(self):
		return self._data['alarm']

	@property
	def alarm_pattern(self):
		return self._data['alarm_pattern']

	def _create_bindings(self, wnd):
		BaseDialog._create_bindings(self, wnd)
		self['dp_date'].Bind(wx.EVT_DATE_CHANGED, self._on_dp_changed)
		self['tc_time'].Bind(wx.lib.masked.EVT_TIMEUPDATE, self._on_time_ctrl)
		self['c_before'].Bind(wx.EVT_CHOICE, self._on_choice_before)

	def _setup(self, alarm, alarm_pattern, no_date):
		_LOG.debug("DlgRemindSettings(%r)", (alarm, alarm_pattern))
		self._data = {'date': None, 'time': None, 'pattern': alarm_pattern,
				'alarm': alarm}
		self['rb_never'].SetValue(True)
		self['tc_time'].BindSpinButton(self['sb_time'])

		c_before = self['c_before']
		c_before.Clear()
		for rem_key, rem_name in enums.REMIND_PATTERNS_LIST:
			c_before.Append(rem_name, rem_key)

		self['dp_date'].SetValidator(ValidatorDate(self._data, 'date'))
		self['tc_time'].SetValidator(ValidatorTime(self._data, 'time'))
		self['rb_never'].SetValue(True)

		if no_date:
			self['rb_datetime'].Enable(False)
			self['tc_time'].Enable(False)
			self['dp_date'].Enable(False)
			self['sb_time'].Enable(False)

		if alarm_pattern:
			for idx in xrange(c_before.GetCount()):
				print alarm_pattern, c_before.GetClientData(idx)
				if c_before.GetClientData(idx) == alarm_pattern:
					c_before.Select(idx)
					self['rb_before'].SetValue(True)
					return
			_LOG.warning("DlgRemindSettings(%r) wrong pattern", alarm_pattern)
		elif alarm and not no_date:
			self._data['date'] = self._data['time'] = alarm
			self['rb_datetime'].SetValue(True)

	def _on_ok(self, evt):
		if not self._wnd.Validate():
			return
		if not self._wnd.TransferDataFromWindow():
			return
		if self['rb_never'].GetValue():
			self._data['alarm_pattern'] = self._data['alarm'] = None
		elif self['rb_datetime'].GetValue():
			self._data['alarm'] = self._data['date'] + self._data['time']
			self._data['alarm_pattern'] = None
		else:
			self._data['alarm'] = None
			c_before = self['c_before']
			self._data['alarm_pattern'] = c_before.GetClientData(
					c_before.GetSelection())
		BaseDialog._on_ok(self, evt)

	def _on_dp_changed(self, _evt):
		if self._wnd.IsActive():
			self['rb_datetime'].SetValue(True)

	def _on_time_ctrl(self, _evt):
		if self._wnd.IsActive():
			self['rb_datetime'].SetValue(True)

	def _on_choice_before(self, _evt):
		if self._wnd.IsActive():
			self['rb_before'].SetValue(True)
