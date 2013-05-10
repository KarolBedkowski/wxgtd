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
import gettext
from datetime import datetime

import wx
try:
	from wx.lib.pubsub.pub import Publisher
except ImportError:
	from wx.lib.pubsub import Publisher

from wxgtd.model import enums
from wxgtd.model import logic
from wxgtd.model import objects as OBJ

from wxgtd.gui.dlg_task import DlgTask
from wxgtd.gui.dlg_checklistitem import DlgChecklistitem
from . import _tasklistctrl as tlc
from ._base_dialog import BaseDialog

_ = gettext.gettext
_LOG = logging.getLogger(__name__)


class DlgReminders(BaseDialog):
	""" Reminders dialog

	Args:
		parent: parent window
	"""

	_dismissed_tasks = set()
	_reminders = []

	def __init__(self, parent):
		BaseDialog.__init__(self, parent, 'dlg_reminders', save_pos=True)
		self._setup()

	def add_tasks(self, tasks):
		for task in tasks:
			if task in self._dismissed_tasks:
				continue
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
		self._task_list_ctrl.Bind(tlc.EVT_LIST_BTN_SNOOZE,
				self._on_task_btn_snooze)
		self._task_list_ctrl.Bind(tlc.EVT_LIST_BTN_DISMISS,
				self._on_task_btn_dismiss)
		self._task_list_ctrl.Bind(wx.EVT_LIST_ITEM_ACTIVATED,
				self._on_items_list_activated)

		Publisher.subscribe(self._on_tasks_update, ('task', 'update'))
		Publisher.subscribe(self._on_tasks_update, ('task', 'delete'))

	def _setup(self):
		self._session = OBJ.Session()

	def _refresh(self):
		self._task_list_ctrl.fill(self._reminders)

	def _on_task_btn_dismiss(self, evt):
		task_uuid = evt.task
		self._dismissed_tasks.add(task_uuid)
		self._remove_task(task_uuid)
		self._refresh()

	def _on_task_btn_snooze(self, evt):
		task_uuid = evt.task
		dlg = wx.SingleChoiceDialog(self._wnd, _("Please select snooze time"),
				_("Snooze task alarm"),
				[pattern[1] for pattern in enums.SNOOZE_PATTERNS],
				wx.CHOICEDLG_STYLE)
		if dlg.ShowModal() == wx.ID_OK:
			pattern = enums.SNOOZE_PATTERNS[dlg.GetSelection()][0]
			task = OBJ.Task.get(self._session, uuid=task_uuid)
			task.alarm = datetime.now() + logic.alarm_pattern_to_time(pattern)
			self._session.commit()
			self._remove_task(task_uuid)
			self._refresh()
			Publisher.sendMessage('task.update', data={'task_uuid': task.uuid})
		dlg.Destroy()

	def _remove_task(self, task_uuid):
		self._reminders = filter(lambda x: x.uuid != task_uuid,
				self._reminders)

	def _on_items_list_activated(self, evt):
		task_uuid, task_type = self._task_list_ctrl.items[evt.GetData()]
		if task_type in (enums.TYPE_PROJECT, enums.TYPE_CHECKLIST):
			# nie powinno być
			return
		if not task_uuid:
			return
		if task_type == enums.TYPE_CHECKLIST_ITEM:
			dlg = DlgChecklistitem.create(task_uuid, self.wnd, task_uuid)
		else:
			dlg = DlgTask.create(task_uuid, self.wnd, task_uuid)
		dlg.run()

	def _on_tasks_update(self, args):
		uuid = args.data['task_uuid']
		if args.topic == ('task', 'delete'):
			self._remove_task(uuid)
		elif args.topic == ('task', 'update'):
			task = OBJ.Task.get(self._session, uuid=uuid)
			if task.completed:
				self._remove_task(uuid)
		self._refresh()
