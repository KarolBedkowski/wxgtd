# -*- coding: utf-8 -*-
""" Dialog showing synchronization progress.

Copyright (c) Karol Będkowski, 2013

This file is part of wxGTD
Licence: GPLv2+
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2013"
__version__ = "2013-04-28"

import logging

import wx
try:
	from wx.lib.pubsub.pub import Publisher  # pylint: disable=E0611
except ImportError:
	from wx.lib.pubsub import Publisher  # pylint: disable=E0611

from ._base_dialog import BaseDialog

_LOG = logging.getLogger(__name__)


class DlgSyncProggress(BaseDialog):
	""" Dialog showing synchronization progress.

	Args:
		parent: parent window
	"""
	def __init__(self, parent):
		self._g_progress = None
		self._tc_progress = None
		BaseDialog.__init__(self, parent, 'dlg_sync_progress', save_pos=False)
		self._setup()

	def update(self, progress, msg):
		""" Update dialog progress and add message.

		Args:
			progress: numeric (0-100) progress
			msg: message to append into window.
		"""
		_LOG.debug("update %r %r", progress, msg)
		self._g_progress.SetValue(max(min(int(progress), 100), 0))
		self._tc_progress.AppendText(msg + '\n')
		self._wnd.Update()

	def mark_finished(self, autoclose=-1):
		""" Set progress finished.

		Args:
			autoclose: if > 0 dialog will be closed after given second.
		"""
		self._g_progress.SetValue(100)
		self[wx.ID_CLOSE].Enable(True)
		if autoclose == 0:
			self._wnd.Close()
		elif autoclose > 0:
			wx.CallLater(autoclose * 1000, self._wnd.Close)

	def run(self, *_args, **_kwargs):
		self._wnd.Show()
		self._wnd.Raise()

	def _load_controls(self, wnd):
		BaseDialog._load_controls(self, wnd)
		self._g_progress = self['g_progress']
		self._tc_progress = self['tc_progress']

	def _setup(self):
		Publisher.subscribe(self._on_update_message, ('sync', 'progress'))
		self[wx.ID_CLOSE].Enable(False)

	def _on_update_message(self, args):
		self.update(*args.data)
