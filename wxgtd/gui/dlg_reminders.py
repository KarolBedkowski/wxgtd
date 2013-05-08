# -*- coding: utf-8 -*-
""" Dialog showing reminders.

Copyright (c) Karol Będkowski, 2013

This file is part of wxGTD
Licence: GPLv2+
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2013"
__version__ = "2013-05-08"

import logging

import wx

from . import _tasklistctrl as tlc
from ._base_dialog import BaseDialog

_LOG = logging.getLogger(__name__)


class DlgReminders(BaseDialog):
	""" Reminders dialog

	Args:
		parent: parent window
	"""

	def __init__(self, parent):
		BaseDialog.__init__(self, parent, 'dlg_reminders', save_pos=True)
		self._setup()

	def add_tasks(self, tasks):
		for task in tasks:
			if task not in self._reminders:
				self._reminders.append(task)
		wx.CallAfter(self._refresh)

	def _load_controls(self, wnd):
		BaseDialog._load_controls(self, wnd)
		wnd.SetExtraStyle(wx.WS_EX_VALIDATE_RECURSIVELY)
		tasklist_panel = self['panel_parent_tasks']
		box = wx.BoxSizer(wx.HORIZONTAL)
		self._task_list_ctrl = tlc.TaskListControl(tasklist_panel,
				buttons=tlc.BUTTON_SNOOZE | tlc.BUTTON_DISMISS)
		box.Add(self._task_list_ctrl, 1, wx.EXPAND)
		tasklist_panel.SetSizer(box)

	def _create_bindings(self):
		BaseDialog._create_bindings(self)

	def _setup(self):
		self._reminders = []

	def _refresh(self):
		self._task_list_ctrl.fill(self._reminders)
