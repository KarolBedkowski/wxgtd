# -*- coding: utf-8 -*-

""" Okno postępu synchronizacji
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2013"
__version__ = "2010-11-25"

import logging

import wx
try:
	from wx.lib.pubsub.pub import Publisher
except ImportError:
	from wx.lib.pubsub import Publisher

from _base_dialog import BaseDialog

_LOG = logging.getLogger(__name__)


class DlgSyncProggress(BaseDialog):
	""" Dlg wyboru daty i czasu (opcjonalnie)
	TODO: maska na timestamp
	"""

	def __init__(self, parent):
		BaseDialog.__init__(self, parent, 'dlg_sync_progress', save_pos=False)
		self._setup()

	def update(self, progress, msg):
		_LOG.debug("update %r %r", progress, msg)
		self._g_progress.SetValue(max(min(int(progress), 100), 0))
		self._tc_progress.AppendText(msg + '\n')
		self._wnd.Update()

	def mark_finished(self, autoclose=-1):
		self._g_progress.SetValue(100)
		self[wx.ID_CLOSE].Enable(True)
		if autoclose == 0:
			self._wnd.Close()
		elif autoclose > 0:
			wx.CallLater(autoclose * 1000, self._wnd.Close)

	def run(self):
		self._wnd.Show()
		self._wnd.Raise()

	def _load_controls(self, wnd):
		BaseDialog._load_controls(self, wnd)
		self._g_progress = self['g_progress']
		self._tc_progress = self['tc_progress']

	def _create_bindings(self):
		BaseDialog._create_bindings(self)

	def _setup(self):
		Publisher.subscribe(self._on_update_message, ('sync', 'progress'))

	def _on_update_message(self, args):
		self.update(*args.data)