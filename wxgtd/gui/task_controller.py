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


from wxgtd.lib.appconfig import AppConfig
from wxgtd.lib import datetimeutils as DTU
from wxgtd.model import objects as OBJ
from wxgtd.model import enums
from wxgtd.logic import task as task_logic

from .dlg_task import DlgTask
from .dlg_checklistitem import DlgChecklistitem
from .dlg_datetime import DlgDateTime
from .dlg_remind_settings import DlgRemindSettings
from .dlg_show_settings import DlgShowSettings
from .dlg_select_tags import DlgSelectTags
from .dlg_repeat_settings import DlgRepeatSettings
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
		if self._task.type == enums.TYPE_CHECKLIST_ITEM:
			self._dialog = DlgChecklistitem(self._parent_wnd, self._task,
					self._session, self)
		else:
			self._dialog = DlgTask(self._parent_wnd, self._task, self._session,
					self)
		self._dialog.run()

	def change_task_type(self):
		if (self._original_task_type != self._task.type
				and (self._task.type == enums.TYPE_CHECKLIST_ITEM
					or self._original_task_type == enums.TYPE_CHECKLIST_ITEM)):
			self._dialog.close()
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
		task = OBJ.Task(type=task_type, parent_uuid=task_parent)
		task_logic.update_task_from_parent(task, task_parent, session,
					AppConfig())
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

	def task_change_due_date(self):
		""" Show dialog and change task due date.

		Args:
			parent_wnd: parent wx window
			task: task to modify
		Returns:
			True if date was changed.
		"""
		if self._task.type == enums.TYPE_PROJECT:
			return self._set_date('due_date_project', 'due_time_set')
		else:
			return self._set_date('due_date', 'due_time_set')

	def task_change_start_date(self):
		""" Show dialog and change task start date.

		Args:
			parent_wnd: parent wx window
			task: task to modify
		Returns:
			True if date was changed.
		"""
		return self._set_date('start_date', 'start_time_set')

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

	def _confirm_change_task_parent(self, parent):
		curr_type = self._task.type
		if parent:  # nowy parent
			if (parent.type == enums.TYPE_CHECKLIST and
					curr_type != enums.TYPE_CHECKLIST_ITEM) or (
					parent.type != enums.TYPE_CHECKLIST and
					curr_type == enums.TYPE_CHECKLIST_ITEM):
				if not mbox.message_box_warning_yesno(self.wnd,
					_("This operation change task and subtasks type.\n"
						"Are you sure?")):
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
						"Are you sure?")):
					return False
		return True

	def _set_date(self, attr_date, attr_time_set):
		""" Wyśweitlenie dlg wyboru daty dla danego atrybutu """
		task = self._task
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
