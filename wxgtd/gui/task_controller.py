# -*- coding: utf-8 -*-
""" Edit task dialog.

Copyright (c) Karol Będkowski, 2013

This file is part of wxGTD
Licence: GPLv2+
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2010-2013"
__version__ = "2010-11-25"

import logging
import gettext

import wx

from wxgtd.lib.appconfig import AppConfig
from wxgtd.lib import datetimeutils as DTU
from wxgtd.model import objects as OBJ
from wxgtd.model import enums
from wxgtd.logic import task as task_logic

from .frame_task import FrameTask
from .frame_checklistitem import FrameChecklistitem
from .dlg_datetime import DlgDateTime
from .dlg_remind_settings import DlgRemindSettings
from .dlg_show_settings import DlgShowSettings
from .dlg_select_tags import DlgSelectTags
from .dlg_repeat_settings import DlgRepeatSettings
from .dlg_projects_tree import DlgProjectTree
from . import message_boxes as mbox

_ = gettext.gettext
_LOG = logging.getLogger(__name__)


class TaskController:
	_controllers = {}

	def __init__(self, parent_wnd, session, task):
		self._session = session or OBJ.Session()
		if isinstance(task, (str, unicode)):
			task = OBJ.Task.get(self._session, uuid=task)
		self._task = task
		self._parent_wnd = parent_wnd
		self._dialog = None
		self._original_task_type = None

	def open_dialog(self):
		_LOG.debug('TaskController.open_dialog(ttype=%r, prev=%r)',
				self._task.type, self._original_task_type)
		self._original_task_type = self._task.type
		if self._dialog is not None:
			self._dialog.run()
			return
		if self._task.type == enums.TYPE_CHECKLIST_ITEM:
			self._dialog = FrameChecklistitem(self._parent_wnd, self._task,
					self._session, self)
		else:
			self._dialog = FrameTask(self._parent_wnd, self._task, self._session,
					self)
		self._dialog.run()

	def change_task_type(self):
		if (self._original_task_type != self._task.type
				and (self._task.type == enums.TYPE_CHECKLIST_ITEM
					or self._original_task_type == enums.TYPE_CHECKLIST_ITEM)):
			self._dialog.close()
			self._dialog = None
			self.open_dialog()

	def close(self):
		if self._task.uuid in self._controllers:
			del self._controllers[self._task.uuid]
		self._session.close()

	@property
	def wnd(self):
		""" Get current wx windows. """
		return (self._dialog and self._dialog.wnd) or self._parent_wnd or None

	@classmethod
	def open_task(cls, parent_wnd, task_uuid):
		if task_uuid in cls._controllers:
			cls._controllers[task_uuid].open_dialog()
			return
		session = OBJ.Session()
		task = OBJ.Task.get(session=session, uuid=task_uuid)
		contr = TaskController(parent_wnd, session, task)
		cls._controllers[task_uuid] = contr
		contr.open_dialog()

	@classmethod
	def new_task(cls, parent_wnd, task_type, task_parent=None):
		session = OBJ.Session()
		parent = None
		if task_parent is not None:
			parent = OBJ.Task.get(session, uuid=task_parent)
		task = OBJ.Task(type=task_type, parent=parent)
		appconfig = AppConfig()
		if task_type == enums.TYPE_CHECKLIST_ITEM:
			task.priority = -1
		else:
			task.priority = appconfig.get('task', 'default_priority', 0)
		task.status = appconfig.get('task', 'default_status', None)
		task.alarm_pattern = appconfig.get('task', 'default_remind', None)
		task.hide_pattern = appconfig.get('task', 'default_hide', None)
		task_logic.update_task_from_parent(task, task_parent, session,
					appconfig)
		contr = TaskController(parent_wnd, session, task)
		contr.open_dialog()

	def confirm_set_task_complete(self):
		return mbox.message_box_question(self.wnd, _("Set task completed?"),
				None, _("Set complete"), _("Close"))

	def delete_task(self):
		""" Delete task with confirmation.

		Returns:
			True after successful delete task.
		"""
		if not mbox.message_box_delete_confirm(self.wnd, _("task")):
			return False
		return task_logic.delete_task(self._task, self._session)

	def delete_tasks(self, tasks_uuid):
		""" Delete multiple task with confirmation.
		Args:
			tasks_uuid: list of tasks uuid to delete
		Returns:
			True after successful delete tasks.
		"""
		if not mbox.message_box_delete_confirm(self.wnd, _("tasks")):
			return False
		return task_logic.delete_task(tasks_uuid, self._session)

	def task_change_due_date(self):
		""" Show dialog and change task due date.

		Args:
			parent_wnd: parent wx window
			task: task to modify
		Returns:
			True if date was changed.
		"""
		if self._task.type == enums.TYPE_PROJECT:
			return self._set_date(self._task, 'due_date_project', 'due_time_set')
		else:
			return self._set_date(self._task, 'due_date', 'due_time_set')

	def task_change_start_date(self):
		""" Show dialog and change task start date.

		Args:
			parent_wnd: parent wx window
			task: task to modify
		Returns:
			True if date was changed.
		"""
		return self._set_date(self._task, 'start_date', 'start_time_set')

	def task_change_remind(self):
		""" Show dialog and change task start date.

		Returns:
			True if date was changed.
		"""
		task = self._task
		alarm = None
		if task.alarm:
			alarm = DTU.datetime2timestamp(task.alarm)
		dlg = DlgRemindSettings(self._parent_wnd, alarm, task.alarm_pattern)
		if dlg.run(True):
			if dlg.alarm:
				task.alarm = DTU.timestamp2datetime(dlg.alarm)
				task.alarm_pattern = None
			else:
				task.alarm = None
				task.alarm_pattern = dlg.alarm_pattern
			task_logic.update_task_alarm(task)
			return True
		return False

	def task_change_hide_until(self):
		""" Show dialog and change task show settings.

		Returns:
			True if date was changed.
		"""
		task = self._task
		date_time = None
		if task.hide_until:
			date_time = DTU.datetime2timestamp(task.hide_until)
		dlg = DlgShowSettings(self._parent_wnd, date_time, task.hide_pattern)
		if dlg.run(True):
			if dlg.datetime:
				task.hide_until = DTU.timestamp2datetime(dlg.datetime)
			else:
				task.hide_until = None
			task.hide_pattern = dlg.pattern
			task_logic.update_task_hide(task)
			return True
		return False

	def task_change_tags(self):
		""" Show dialog and change task's tags.

		Returns:
			True if tags was changed.
		"""
		task = self._task
		tags_uuids = [tasktag.tag_uuid for tasktag in task.tags]
		dlg = DlgSelectTags(self._parent_wnd, tags_uuids)
		if dlg.run(True):
			new_tags = dlg.selected_tags
			for tasktag in list(task.tags):
				if tasktag.tag_uuid not in new_tags:
					task.tags.delete(tasktag)  # pylint: disable=E1103
				else:
					new_tags.remove(tasktag.tag_uuid)
			for tag_uuid in new_tags:
				tasktag = OBJ.TaskTag()
				tasktag.tag = self._session.query(  # pylint: disable=E1101
						OBJ.Tag).filter_by(uuid=tag_uuid).first()
				task.tags.append(tasktag)  # pylint: disable=E1103
			return True
		return False

	def task_change_repeat(self):
		""" Show dialog and change task's repeat settings.

		Returns:
			True if task was changed.
		"""
		task = self._task
		dlg = DlgRepeatSettings(self._parent_wnd, task.repeat_pattern,
				task.repeat_from)
		if dlg.run(True):
			task.repeat_from = dlg.repeat_from
			task.repeat_pattern = dlg.pattern
			return True
		return False

	def task_change_parent(self, parent_uuid):
		""" Change current task parent with confirmation.

		Args:
			parent_uuid: destination parent UUID
		Returns:
			True if parent was changed.
		"""
		parent = None
		if parent_uuid:
			parent = OBJ.Task.get(self._session, uuid=parent_uuid)
		if not self._confirm_change_task_parent(parent):
			return False
		return task_logic.change_task_parent(self._task, parent, self._session)

	def task_change_type(self):
		""" Change current task type with confirmation when this action may
		affect subtasks.

		Returns:
			True on change.
		"""
		parent_type = self._task.parent.type if self._task.parent else None
		if parent_type == enums.TYPE_CHECKLIST:
			# nie można zmienić typu z TYPE_CHECKLIST_ITEM
			self._task.type = enums.TYPE_CHECKLIST_ITEM
			return True
		values = [enums.TYPE_TASK, enums.TYPE_CALL, enums.TYPE_EMAIL,
				enums.TYPE_SMS, enums.TYPE_RETURN_CALL, enums.TYPE_PROJECT,
				enums.TYPE_CHECKLIST]
		choices = [enums.TYPES[val] for val in values]
		dlg = wx.SingleChoiceDialog(self.wnd, _("Change task type to:"),
				_("Task"), choices, wx.CHOICEDLG_STYLE)
		new_type = self._task.type
		if dlg.ShowModal() == wx.ID_OK:
			new_type = values[dlg.GetSelection()]
		dlg.Destroy()
		if new_type == self._task.type:
			return False
		if (self._task.type in (enums.TYPE_PROJECT, enums.TYPE_CHECKLIST)
				or new_type in (enums.TYPE_PROJECT, enums.TYPE_CHECKLIST)):
			if not self._confirm_change_task_type():
				return False
		self._task.type = new_type
		return True

	def tasks_change_status(self, tasks_uuid):
		""" Change status in given tasks; display window with statuses

		Args:
			tasks_uuid: list of tasks uuid to change
		Returns:
			True when success.
		"""
		values = sorted(enums.STATUSES.keys())
		choices = [enums.STATUSES[val] for val in values]
		dlg = wx.SingleChoiceDialog(self.wnd, _("Change tasks status to:"),
				_("Tasks"), choices, wx.CHOICEDLG_STYLE)
		new_status = None
		if dlg.ShowModal() == wx.ID_OK:
			new_status = values[dlg.GetSelection()]
		dlg.Destroy()
		if new_status is None:
			return False
		tasks_to_save = []
		for task_uuid in tasks_uuid:
			task = OBJ.Task.get(self._session, uuid=task_uuid)
			if not task:
				_LOG.warn("tasks_change_status: task %r not found", task_uuid)
				continue
			if task.status == new_status:
				continue
			task.status = new_status
			tasks_to_save.append(task)
		if tasks_to_save:
			return task_logic.save_modified_tasks(tasks_to_save, self._session)
		return False

	def tasks_change_context(self, tasks_uuid):
		""" Change context in given tasks; display window with defined context
		to select.

		Args:
			tasks_uuid: list of tasks uuid to change
		Returns:
			True when success.
		"""
		values, choices = [None], [_("No Context")]
		for context in OBJ.Context.all():
			values.append(context.uuid)
			choices.append(context.title)
		dlg = wx.SingleChoiceDialog(self.wnd, _("Change tasks context to:"),
				_("Tasks"), choices, wx.CHOICEDLG_STYLE)
		context = -1
		if dlg.ShowModal() == wx.ID_OK:
			context = values[dlg.GetSelection()]
		dlg.Destroy()
		if context == -1:
			return False
		tasks_to_save = []
		for task_uuid in tasks_uuid:
			task = OBJ.Task.get(self._session, uuid=task_uuid)
			if not task:
				_LOG.warn("tasks_change_status: task %r not found", task_uuid)
				continue
			if task.context_uuid != context:
				task.context_uuid = context
				tasks_to_save.append(task)
		if tasks_to_save:
			return task_logic.save_modified_tasks(tasks_to_save, self._session)
		return False

	def tasks_change_project(self, tasks_uuid):
		""" Move tasks to project/checklist; display window with defined
		projects to select.

		Args:
			tasks_uuid: list of tasks uuid to change
		Returns:
			True when success.
		"""
		dlg = DlgProjectTree(self.wnd)
		if not dlg.run(modal=True):
			return False
		parent_uuid = dlg.selected
		tasks_to_save = []
		for task_uuid in tasks_uuid:
			task = OBJ.Task.get(self._session, uuid=task_uuid)
			if not task:
				_LOG.warn("tasks_change_status: task %r not found", task_uuid)
				continue
			if task.parent_uuid != parent_uuid:
				if task_logic.change_task_parent(task, parent_uuid,
						self._session):
					tasks_to_save.append(task)
		if tasks_to_save:
			return task_logic.save_modified_tasks(tasks_to_save, self._session)
		return False

	def tasks_change_folder(self, tasks_uuid):
		""" Change folder in given tasks; display window with defined folders
		to select.

		Args:
			tasks_uuid: list of tasks uuid to change
		Returns:
			True when success.
		"""
		values, choices = [None], [_("No Folder")]
		for folder in OBJ.Folder.all():
			values.append(folder.uuid)
			choices.append(folder.title)
		dlg = wx.SingleChoiceDialog(self.wnd, _("Change tasks folder to:"),
				_("Tasks"), choices, wx.CHOICEDLG_STYLE)
		folder = -1
		if dlg.ShowModal() == wx.ID_OK:
			folder = values[dlg.GetSelection()]
		dlg.Destroy()
		if folder == -1:
			return False
		tasks_to_save = []
		for task_uuid in tasks_uuid:
			task = OBJ.Task.get(self._session, uuid=task_uuid)
			if not task:
				_LOG.warn("tasks_change_status: task %r not found", task_uuid)
				continue
			if task.folder_uuid != folder:
				task.folder_uuid = folder
				tasks_to_save.append(task)
		if tasks_to_save:
			return task_logic.save_modified_tasks(tasks_to_save, self._session)
		return False

	def tasks_change_start_date(self, tasks_uuid):
		""" Change start date for given tasks. """
		task1 = OBJ.Task.get(self._session, uuid=tasks_uuid[0])
		if self._set_date(task1, 'start_date', 'start_time_set'):
			tasks_to_save = [task1]
			for task_uuid in tasks_uuid[1:]:
				task = OBJ.Task.get(self._session, uuid=task_uuid)
				if (task.start_date != task1.start_date or
						task.start_time_set != task1.start_time_set):
					task.start_date = task1.start_date
					task.start_time_set = task1.start_time_set
					tasks_to_save.append(task)
			return task_logic.save_modified_tasks(tasks_to_save, self._session)
		return False

	def tasks_change_due_date(self, tasks_uuid):
		""" Change due date for given tasks. """
		task1 = OBJ.Task.get(self._session, uuid=tasks_uuid[0])
		task1_due_attr = 'due_date'
		if task1.type == enums.TYPE_PROJECT:
			task1_due_attr = 'due_date_project',
		if self._set_date(task1, task1_due_attr, 'due_time_set'):
			tasks_to_save = [task1]
			due = (task1.due_date_project if task1.type == enums.TYPE_PROJECT
					else task1.due_date)
			for task_uuid in tasks_uuid[1:]:
				task = OBJ.Task.get(self._session, uuid=task_uuid)
				if task.type == enums.TYPE_PROJECT:
					if (task.start_time_set != task1.start_time_set or
							task.due_date_project != due):
						task.due_date_project = due
						task.due_time_set = task1.due_time_set
						tasks_to_save.append(task)
				else:
					if (task.start_time_set != task1.start_time_set or
							task.due_date != due):
						task.due_date = due
						task.due_time_set = task1.due_time_set
						tasks_to_save.append(task)
			return task_logic.save_modified_tasks(tasks_to_save, self._session)
		return False

	def tasks_change_remind(self, tasks_uuid):
		""" Show dialog and change given tasks start date.

		Args:
			tasks_uuid: task to change
		Returns:
			True if date was changed.
		"""
		task = OBJ.Task.get(self._session, uuid=tasks_uuid[0])
		alarm = None
		if task.alarm:
			alarm = DTU.datetime2timestamp(task.alarm)
		dlg = DlgRemindSettings(self._parent_wnd, alarm, task.alarm_pattern)
		if not dlg.run(True):
			return False
		if dlg.alarm:
			alarm = DTU.timestamp2datetime(dlg.alarm)
			alarm_pattern = None
		else:
			alarm = None
			alarm_pattern = dlg.alarm_pattern
		task.alarm = alarm
		task.alarm_pattern = alarm_pattern
		task_logic.update_task_alarm(task)
		tasks_to_save = [task]
		for task_uuid in tasks_uuid[1:]:
			task = OBJ.Task.get(self._session, uuid=task_uuid)
			task.alarm = alarm
			task.alarm_pattern = alarm_pattern
			task_logic.update_task_alarm(task)
			tasks_to_save.append(task)
		return task_logic.save_modified_tasks(tasks_to_save, self._session)

	def tasks_change_hide_until(self, tasks_uuid):
		""" Show dialog and change given tasks show settings.

		Args:
			tasks_uuid: task to change
		Returns:
			True if date was changed.
		"""
		task = OBJ.Task.get(self._session, uuid=tasks_uuid[0])
		date_time = None
		if task.hide_until:
			date_time = DTU.datetime2timestamp(task.hide_until)
		dlg = DlgShowSettings(self._parent_wnd, date_time, task.hide_pattern)
		if not dlg.run(True):
			return
		hide_until = None
		hide_pattern = dlg.pattern
		if dlg.datetime:
			hide_until = DTU.timestamp2datetime(dlg.datetime)
		tasks_to_save = []
		for task_uuid in tasks_uuid:
			task = OBJ.Task.get(self._session, uuid=task_uuid)
			task.hide_until = hide_until
			task.hide_pattern = hide_pattern
			task_logic.update_task_hide(task)
			tasks_to_save.append(task)
		return task_logic.save_modified_tasks(tasks_to_save, self._session)

	def _confirm_change_task_parent(self, parent):
		curr_type = self._task.type
		if parent:  # nowy parent
			if (parent.type == enums.TYPE_CHECKLIST and
					curr_type != enums.TYPE_CHECKLIST_ITEM) or (
					parent.type != enums.TYPE_CHECKLIST and
					curr_type == enums.TYPE_CHECKLIST_ITEM):
				if not mbox.message_box_warning_yesno(self.wnd,
					_("This operation change task and subtasks type.\n"
						"Continue change??")):
					return False
		else:  # brak nowego parenta
			if curr_type in (enums.TYPE_CHECKLIST, enums.TYPE_PROJECT):
				if not mbox.message_box_warning_yesno(self.wnd,
						_("This operation change all subtasks to simple"
							" tasks\nAre you sure?")):
					return False
			elif curr_type == enums.TYPE_CHECKLIST_ITEM:
				if not mbox.message_box_warning_yesno(self.wnd,
					_("This operation change task and subtasks type.\n"
						"Continue change??")):
					return False
		return True

	def tasks_set_completed_status(self, tasks_uuid, compl):
		if compl:
			if not mbox.message_box_question(self.wnd, _("Set tasks completed?"),
					None, _("Set complete"), _("Close")):
				return False
		else:
			if not mbox.message_box_question(self.wnd,
					_("Set tasks not completed?"), None, _("Set complete"),
					_("Close")):
				return False
		tasks_to_save = []
		for task_uuid in tasks_uuid:
			task = OBJ.Task.get(self._session, uuid=task_uuid)
			if not task:
				_LOG.warn("tasks_set_completed_status: task %r not found", task_uuid)
				continue
			if task.task_completed != compl:
				if compl:
					task_logic.complete_task(task, self._session)
				else:
					task.task_completed = False
				tasks_to_save.append(task)
		if tasks_to_save:
			return task_logic.save_modified_tasks(tasks_to_save, self._session)
		return False

	def tasks_set_starred_flag(self, tasks_uuid, starred):
		""" Set starred flag for given tasks. """
		tasks_to_save = []
		for task_uuid in tasks_uuid:
			task = OBJ.Task.get(self._session, uuid=task_uuid)
			if not task:
				_LOG.warn("tasks_set_completed_status: task %r not found", task_uuid)
				continue
			task.starred = bool(starred)
			tasks_to_save.append(task)
		if tasks_to_save:
			return task_logic.save_modified_tasks(tasks_to_save, self._session)
		return False

	def _confirm_change_task_type(self):
		return mbox.message_box_warning_yesno(self.wnd,
			_("This operation change task and subtasks type.\n"
				"Continue change?"))

	def _set_date(self, task, attr_date, attr_time_set):
		""" Wyśweitlenie dlg wyboru daty dla danego atrybutu """
		value = getattr(task, attr_date)
		if value:
			value = DTU.datetime2timestamp(value)
		dlg = DlgDateTime(self._parent_wnd, value, getattr(task, attr_time_set))
		if dlg.run(True):
			date = None
			if dlg.timestamp:
				date = DTU.timestamp2datetime(dlg.timestamp)
			setattr(task, attr_date, date)
			setattr(task, attr_time_set, dlg.is_time_set)
			return True
		return False
