# -*- coding: utf-8 -*-
""" Dialog for selecting date and time.

Copyright (c) Karol Będkowski, 2013

This file is part of wxGTD
Licence: GPLv2+
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2013"
__version__ = "2013-04-28"

import logging

import wx
import wx.calendar

from wxgtd.wxtools.validators import ValidatorDate, ValidatorTime

from ._base_dialog import BaseDialog

_LOG = logging.getLogger(__name__)


class DlgDateTime(BaseDialog):
	""" Dialog for edit date and time.
	TODO: maska na timestamp

	Args:
		parent: parent window
		timestamp: date and time as long or datetime
		timeset: boolean - is time is set.
	"""

	def __init__(self, parent, timestamp, timeset):
		BaseDialog.__init__(self, parent, 'dlg_datetime', save_pos=False)
		self._setup(timestamp, timeset)
		self._timeset = timeset
		self._timestamp = timestamp

	@property
	def timestamp(self):
		return self._timestamp

	@property
	def is_time_set(self):
		return self._timeset

	def _load_controls(self, wnd):
		BaseDialog._load_controls(self, wnd)
		wnd.SetExtraStyle(wx.WS_EX_VALIDATE_RECURSIVELY)

	def _create_bindings(self):
		BaseDialog._create_bindings(self)
		self['cc_date'].Bind(wx.calendar.EVT_CALENDAR, self._on_calendar)
		self['cc_date'].Bind(wx.calendar.EVT_CALENDAR_SEL_CHANGED,
				self._on_calendar)
		self['tc_time'].Bind(wx.lib.masked.EVT_TIMEUPDATE, self._on_time_ctrl)
		self['cb_set_time'].Bind(wx.EVT_CHECKBOX, self._on_cb_set_time)

	def _setup(self, timestamp, timeset):
		_LOG.debug("DlgDateTime(%r)", timestamp)
		self._values = {'date': timestamp,
				'time': (timestamp if timeset else 0)}
		self['cc_date'].SetValidator(ValidatorDate(self._values, 'date'))
		self['tc_time'].SetValidator(ValidatorTime(self._values, 'time'))
		self['tc_time'].BindSpinButton(self['sb_time'])
		if timestamp:
			self['rb_date'].SetValue(True)
		self['cb_set_time'].SetValue(bool(timeset))

	def _on_ok(self, evt):
		if self['rb_no_date'].GetValue():
			# nie wybrano daty
			self._timestamp = None
			self._timeset = None
			BaseDialog._on_ok(self, evt)
			return
		if not self._wnd.Validate():
			return
		if not self._wnd.TransferDataFromWindow():
			return
		self._timestamp = int(self._values['date'])
		self._timeset = self['cb_set_time'].GetValue()
		if self._timeset:
			self._timestamp += int(self._values['time'])
		BaseDialog._on_ok(self, evt)

	def _on_calendar(self, _evt):
		self['rb_date'].SetValue(True)

	def _on_time_ctrl(self, _evt):
		self['rb_date'].SetValue(True)
		self['cb_set_time'].SetValue(True)

	def _on_cb_set_time(self, _evt):
		self['rb_date'].SetValue(True)
