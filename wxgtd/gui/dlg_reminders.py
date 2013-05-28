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
	from wx.lib.pubsub import Publisher  # pylint: disable=E0611

from wxgtd.logic import task as task_logic
from wxgtd.model import enums
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

	def __init__(self, parent, session):
		self._task_list_ctrl = None
		BaseDialog.__init__(self, parent, 'dlg_reminders', save_pos=True)
		self._obj_key = 'dlg_reminders'
		self._setup(session)
		self._refresh()

	@classmethod
	def check(cls, parent_wnd, session):
		tasks = OBJ.Task.select_reminders(None, session)
		# filter tasks
		tasks_to_show = []
		for task in tasks:
			if task.completed:
				_LOG.warn('DlgReminders.check completed %r', task)
				continue
			tasks_to_show.append(task)
		if tasks_to_show:
			dlg = cls._windows.get('dlg_reminders')
			if not dlg:
				dlg = cls._windows['dlg_reminders'] = DlgReminders(parent_wnd,
						session)
			dlg.run()
			dlg.load_tasks(tasks)
			wx.CallAfter(dlg.wnd.Raise)
		return len(tasks_to_show) > 0

	def load_tasks(self, tasks):
		_LOG.debug('DlgReminders.load_tasks(%r)', tasks)
		self._reminders = tasks
		self._refresh()

	def _load_controls(self, wnd):
		BaseDialog._load_controls(self, wnd)
		wnd.SetExtraStyle(wx.WS_EX_VALIDATE_RECURSIVELY)
		tasklist_panel = self['panel_parent_tasks']
		box = wx.BoxSizer(wx.HORIZONTAL)
		self._task_list_ctrl = tlc.TaskListControl(tasklist_panel,
				buttons=tlc.BUTTON_SNOOZE | tlc.BUTTON_DISMISS)
		box.Add(self._task_list_ctrl, 1, wx.EXPAND)
		tasklist_panel.SetSizer(box)

	def _create_bindings(self, wnd):
		BaseDialog._create_bindings(self, wnd)
		self._task_list_ctrl.Bind(tlc.EVT_LIST_BTN_SNOOZE,
				self._on_task_btn_snooze)
		self._task_list_ctrl.Bind(tlc.EVT_LIST_BTN_DISMISS,
				self._on_task_btn_dismiss)
		self._task_list_ctrl.Bind(wx.EVT_LIST_ITEM_ACTIVATED,
				self._on_items_list_activated)

		Publisher().subscribe(self._on_tasks_update, ('task', 'update'))
		Publisher().subscribe(self._on_tasks_update, ('task', 'delete'))

	def _setup(self, session):
		self._reminders = []
		self._session = session or OBJ.Session()

	def _refresh(self):
		self._task_list_ctrl.fill(self._reminders)

	def _on_task_btn_dismiss(self, evt):
		task_uuid = evt.task
		task = OBJ.Task.get(self._session, uuid=task_uuid)
		task.alarm = None
		task.update_modify_time()
		self._session.commit()
		Publisher().sendMessage('task.update', data={'task_uuid': task.uuid})

	def _on_task_btn_snooze(self, evt):
		task_uuid = evt.task
		dlg = wx.SingleChoiceDialog(self._wnd, _("Please select snooze time"),
				_("Snooze task alarm"),
				[pattern[1] for pattern in enums.SNOOZE_PATTERNS],
				wx.CHOICEDLG_STYLE)
		if dlg.ShowModal() == wx.ID_OK:
			pattern = enums.SNOOZE_PATTERNS[dlg.GetSelection()][0]
			task = OBJ.Task.get(self._session, uuid=task_uuid)
			task.alarm = datetime.utcnow() + task_logic.alarm_pattern_to_time(pattern)
			task.update_modify_time()
			self._session.commit()
			Publisher().sendMessage('task.update', data={'task_uuid': task.uuid})
		dlg.Destroy()

	def _remove_task(self, task_uuid):
		task_idx = [idx for idx, task in enumerate(self._reminders)
				if task.uuid == task_uuid]
		if task_idx:
			del self._reminders[task_idx[0]]
		if not self._reminders:
			self.wnd.Close()

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
		_LOG.debug('DlgReminders._on_tasks_update(%r)', args)
		uuid = args.data['task_uuid']
		if args.topic == ('task', 'delete'):
			self._remove_task(uuid)
		elif args.topic == ('task', 'update'):
			task = OBJ.Task.get(self._session, uuid=uuid)
			if task.completed or not task.alarm or task.alarm > datetime.utcnow():
				self._remove_task(uuid)
		self._refresh()
