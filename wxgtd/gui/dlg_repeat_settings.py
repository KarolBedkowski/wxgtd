# -*- coding: utf-8 -*-

""" Klasa bazowa dla wszystkich dlg.
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2010-2013"
__version__ = "2010-11-25"

import logging

import wx

from wxgtd.model import enums

from _base_dialog import BaseDialog

_LOG = logging.getLogger(__name__)


class DlgRepeatSettings(BaseDialog):
	""" Dlg wyboru ustawień dot. przypomnien
	"""

	def __init__(self, parent, pattern, repeat_from):
		""" Konst
		parent - okno nadrzędne
		alarm - czas jako long
		alarm_pattern - opis przpomnienia (z enums.REMAIND_PATTERNS)
		"""
		self._data = {'pattern': pattern, 'from': repeat_from}
		BaseDialog.__init__(self, parent, 'dlg_repeat_settings', save_pos=False)
		self._setup(pattern, repeat_from)

	@property
	def repeat_from(self):
		return self._data['from']

	@property
	def pattern(self):
		return self._data['pattern']

	def _load_controls(self, wnd):
		BaseDialog._load_controls(self, wnd)
		wnd.SetExtraStyle(wx.WS_EX_VALIDATE_RECURSIVELY)
		c_every = self['c_every']
		for rem_key, rem_name in enums.REPEAT_PATTERN_LIST:
			c_every.Append(rem_name, rem_key)

	def _create_bindings(self):
		BaseDialog._create_bindings(self)

	def _setup(self, pattern, repeat_from):
		_LOG.debug("DlgRemaindSettings(%r)", (pattern, repeat_from))
		self['rb_never'].SetValue(True)
		self['rb_completion'].SetValue(bool(repeat_from))
		if pattern:
			c_every = self['c_every']
			for idx in xrange(c_every.GetCount()):
				if c_every.GetClientData(idx) == pattern:
					c_every.Select(idx)
					self['rb_every'].SetValue(True)
					return
			# brak znanego typu
			self['tc_pattern'].SetValue(pattern)
			self['rb_custom'].SetValue(True)

	def _on_ok(self, evt):
		self._data['from'] = 1 if self['rb_completion'].GetValue() else 0
		if self['rb_never'].GetValue():
			self._data['pattern'] = None
		elif self['rb_custom'].GetValue():
			self._data['pattern'] = self['tc_pattern'].GetValue()
		else:
			c_every = self['c_every']
			self._data['pattern'] = c_every.GetClientData(
					c_every.GetSelection())
		BaseDialog._on_ok(self, evt)
