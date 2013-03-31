# -*- coding: utf-8 -*-

""" Klasa bazowa dla wszystkich dlg.
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2010-2013"
__version__ = "2010-11-25"

import logging

import wx

from wxgtd.wxtools.validators import ValidatorDate, ValidatorTime

from _base_dialog import BaseDialog

_LOG = logging.getLogger(__name__)


class DlgDateTime(BaseDialog):
	"""
	Dlg wyboru daty i czasu (opcjonalnie)
	"""

	def __init__(self, parent, timestamp, timeset):
		BaseDialog.__init__(self, parent, 'dlg_datetime')
		self._setup(timestamp, timeset)
		self._timeset = timeset
		self._timestamp = timestamp

	@property
	def timestamp(self):
		return self._timestamp

	@property
	def is_time_set(self):
		return self._

	def _load_controls(self, wnd):
		BaseDialog._load_controls(self, wnd)
		wnd.SetExtraStyle(wx.WS_EX_VALIDATE_RECURSIVELY)

	def _create_bindings(self):
		BaseDialog._create_bindings(self)

	def _setup(self, timestamp, timeset):
		_LOG.debug("DlgDateTime(%r)", timestamp)
		self._values = {'date': timestamp,
				'time': (timestamp if timeset else 0)}
		if timestamp:
			self['cc_date'].SetValidator(ValidatorDate(self._values, 'date'))
			self['tc_time'].SetValidator(ValidatorTime(self._values, 'time'))
			self['rb_date'].SetValue(True)
			self['cb_set_time'].SetValue(timeset)

	def _on_ok(self, evt):
		if self['rb_no_date'].GetValue():
			# nie wybrano daty
			self._timestamp = None
			BaseDialog._on_ok(evt)
			return
		if not self._wnd.Validate():
			return
		if not self._wnd.TransferDataFromWindow():
			return
		self._timestamp = int(self._values['date'])
		if self['cb_set_time'].GetValue():
			self._timestamp += int(self._values['time'])
		BaseDialog._on_ok(self, evt)
