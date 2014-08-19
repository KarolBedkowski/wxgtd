# -*- coding: utf-8 -*-
""" Task show options dialog.

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


class DlgShowSettings(BaseDialog):
	""" Task show options dialog.

	Args:
		parent: parent windows
		date: date when show task
		pattern: pattern to set date dynamically (enums.HIDE_PATTERNS)
		no_date: don't allow set exact date
	"""

	def __init__(self, parent, date, pattern, no_date=False):
		BaseDialog.__init__(self, parent, 'dlg_show_settings', save_pos=False)
		self._setup(date, pattern, no_date)

	@property
	def datetime(self):
		return self._data['datetime']

	@property
	def pattern(self):
		return self._data['pattern']

	def _create_bindings(self, wnd):
		BaseDialog._create_bindings(self, wnd)
		self['dp_date'].Bind(wx.EVT_DATE_CHANGED, self._on_dp_changed)
		self['tc_time'].Bind(wx.lib.masked.EVT_TIMEUPDATE, self._on_time_ctrl)
		self['c_pattern'].Bind(wx.EVT_CHOICE, self._on_choice_pattern)

	def _setup(self, date, pattern, no_date):
		_LOG.debug("DlgShowSettings(%r)", (date, pattern))
		self._data = {'date': None, 'time': None, 'pattern': pattern,
				'datetime': date}

		self['dp_date'].SetValidator(ValidatorDate(self._data, 'date'))
		self['tc_time'].SetValidator(ValidatorTime(self._data, 'time'))
		self['tc_time'].BindSpinButton(self['sb_time'])

		if no_date:
			self['rb_datetime'].Enable(False)
			self['tc_time'].Enable(False)
			self['dp_date'].Enable(False)
			self['sb_time'].Enable(False)

		c_pattern = self['c_pattern']
		for rem_key, rem_name in enums.HIDE_PATTERNS_LIST:
			if rem_key != "given date":
				c_pattern.Append(rem_name, rem_key)

		self['rb_always'].SetValue(True)
		if pattern and pattern != "given date":
			c_pattern = self['c_pattern']
			for idx in xrange(c_pattern.GetCount()):
				if c_pattern.GetClientData(idx) == pattern:
					c_pattern.Select(idx)
					self['rb_before'].SetValue(True)
					return
			_LOG.warning("DlgShowSettings(%r) wrong pattern", pattern)
		if date and not no_date:
			self._data['date'] = self._data['time'] = date
			self['rb_datetime'].SetValue(True)

	def _on_ok(self, evt):
		if not self._wnd.Validate():
			return
		if not self._wnd.TransferDataFromWindow():
			return
		if self['rb_always'].GetValue():
			self._data['pattern'] = self._data['datetime'] = None
		elif self['rb_datetime'].GetValue():
			self._data['datetime'] = self._data['date'] + self._data['time']
			self._data['pattern'] = 'given date'
		else:
			self._data['datetime'] = None
			c_pattern = self['c_pattern']
			self._data['pattern'] = c_pattern.GetClientData(
					c_pattern.GetSelection())
		BaseDialog._on_ok(self, evt)

	def _on_dp_changed(self, _evt):
		if self._wnd.IsActive():
			self['rb_datetime'].SetValue(True)

	def _on_time_ctrl(self, _evt):
		if self._wnd.IsActive():
			self['rb_datetime'].SetValue(True)

	def _on_choice_pattern(self, _evt):
		if self._wnd.IsActive():
			self['rb_before'].SetValue(True)
