# -*- coding: utf-8 -*-

""" Klasa bazowa dla wszystkich dlg.
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2010-2013"
__version__ = "2010-11-25"

import logging

import wx

from wxgtd.wxtools.validators import ValidatorDate, ValidatorTime
from wxgtd.model import enums

from _base_dialog import BaseDialog

_LOG = logging.getLogger(__name__)


class DlgRemaindSettings(BaseDialog):
	""" Dlg wyboru ustawień dot. przypomnien
	"""

	def __init__(self, parent, alarm, alarm_pattern):
		""" Konst
		parent - okno nadrzędne
		alarm - czas jako long
		alarm_pattern - opis przpomnienia (z enums.REMAIND_PATTERNS)
		"""
		self._data = {'date': None, 'time': None, 'pattern': alarm_pattern,
				'alarm': alarm}
		BaseDialog.__init__(self, parent, 'dlg_remaind_settings')
		self._setup(alarm, alarm_pattern)

	@property
	def alarm(self):
		return self._data['alarm']

	@property
	def alarm_pattern(self):
		return self._data['alarm_pattern']

	def _load_controls(self, wnd):
		BaseDialog._load_controls(self, wnd)
		wnd.SetExtraStyle(wx.WS_EX_VALIDATE_RECURSIVELY)

		self['dp_date'].SetValidator(ValidatorDate(self._data, 'date'))
		self['tc_time'].SetValidator(ValidatorTime(self._data, 'time'))

		c_before = self['c_before']
		for rem_key, rem_name in enums.REMAIND_PATTERNS_LIST:
			c_before.Append(rem_name, rem_key)

	def _create_bindings(self):
		BaseDialog._create_bindings(self)

	def _setup(self, alarm, alarm_pattern):
		_LOG.debug("DlgRemaindSettings(%r)", (alarm, alarm_pattern))
		self['rb_never'].SetValue(True)
		if alarm:
			self._data['date'] = self._data['time'] = alarm
			if not alarm_pattern or alarm_pattern == 'due':
				self['rb_datetime'].SetValue(True)
				return
		if alarm_pattern:
			c_before = self['c_before']
			for idx in xrange(c_before.GetCount()):
				if c_before.GetClientData(idx) == alarm_pattern:
					c_before.Select(idx)
					self['rb_before'].SetValue(True)
					return

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
