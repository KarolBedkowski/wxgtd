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
import datetime

import wx
import wx.calendar

from wxgtd.wxtools.validators import ValidatorDate, ValidatorTime

from ._base_dialog import BaseDialog

_LOG = logging.getLogger(__name__)


class DlgDateTime(BaseDialog):
	""" Dialog for edit date and time.

	Args:
		parent: parent window
		timestamp: date and time as long or datetime
		timeset: boolean - is time is set.
	"""

	def __init__(self, parent, timestamp, timeset):
		BaseDialog.__init__(self, parent, 'dlg_datetime', save_pos=False)
		self._timeset = timeset
		self._timestamp = timestamp
		self._values = {'date': timestamp,
				'time': (timestamp if timeset else 0)}
		self._setup(timestamp, timeset)

	@property
	def timestamp(self):
		return self._timestamp

	@property
	def is_time_set(self):
		return self._timeset

	def _load_controls(self, wnd):
		BaseDialog._load_controls(self, wnd)
		wnd.SetExtraStyle(wx.WS_EX_VALIDATE_RECURSIVELY)

	def _create_bindings(self, wnd):
		BaseDialog._create_bindings(self, wnd)
		self['cc_date'].Bind(wx.calendar.EVT_CALENDAR, self._on_calendar)
		self['cc_date'].Bind(wx.calendar.EVT_CALENDAR_SEL_CHANGED,
				self._on_calendar)
		self['tc_time'].Bind(wx.lib.masked.EVT_TIMEUPDATE, self._on_time_ctrl)
		self['cb_set_time'].Bind(wx.EVT_CHECKBOX, self._on_cb_set_time)
		self['btn_today'].Bind(wx.EVT_BUTTON, self._on_btn_today)
		self['btn_tomorrow'].Bind(wx.EVT_BUTTON, self._on_btn_tomorrow)
		self['btn_next_week'].Bind(wx.EVT_BUTTON, self._on_btn_next_week)

	def _setup(self, timestamp, timeset):
		_LOG.debug("DlgDateTime(%r)", timestamp)
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

	def _on_btn_today(self, _evt):
		self._set_datetime(datetime.datetime.now())

	def _on_btn_tomorrow(self, _evt):
		self._set_datetime(datetime.datetime.now() + datetime.timedelta(days=1))

	def _on_btn_next_week(self, _evt):
		self._set_datetime(datetime.datetime.now() + datetime.timedelta(days=7))

	def _set_datetime(self, date):
		self['cc_date'].SetDate(wx.DateTimeFromDMY(
				date.day, date.month - 1, date.year))
		if self['cb_set_time'].GetValue():
			self['tc_time'].SetValue("%02d:%02d:%02d" % (
					date.hour, date.minute, date.second))
		else:
			self['tc_time'].SetValue("00:00:00")
			self['cb_set_time'].SetValue(False)
