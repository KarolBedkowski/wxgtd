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

_ = gettext.gettext
_LOG = logging.getLogger(__name__)


class TaskDialogControler:
	_controllers = {}

	def __init__(self, parent_wnd, session, task):
		self._session = session or OBJ.Session()
		self._task = task
		self._parent_wnd = parent_wnd
		self._dialog = None
		self._original_task_type = None

	def open_dialog(self):
		_LOG.debug('TaskDialogControler.open_dialog(ttype=%r, prev=%r)',
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

	@classmethod
	def open_task(cls, parent_wnd, task_uuid):
		if task_uuid in cls._controllers:
			cls._controllers[task_uuid].open_dialog()
			return
		session = OBJ.Session()
		task = OBJ.Task.get(session=session, uuid=task_uuid)
		contr = TaskDialogControler(parent_wnd, session, task)
		cls._controllers[task_uuid] = contr
		contr.open_dialog()

	@classmethod
	def new_task(cls, parent_wnd, task_type, task_parent=None):
		session = OBJ.Session()
		task = OBJ.Task(type=task_type, parent_uuid=task_parent)
		task_logic.update_task_from_parent(task, task_parent, session,
					AppConfig())
		contr = TaskDialogControler(parent_wnd, session, task)
		contr.open_dialog()

	@classmethod
	def task_change_due_date(cls, parent_wnd, task):
		""" Show dialog and change task due date.

		Args:
			parent_wnd: parent wx window
			task: task to modify
		Returns:
			True if date was changed.
		"""
		if task.type == enums.TYPE_PROJECT:
			return cls._set_date(parent_wnd, task, 'due_date_project',
					'due_time_set')
		else:
			return cls._set_date(parent_wnd, task, 'due_date', 'due_time_set')

	@classmethod
	def task_change_start_date(cls, parent_wnd, task):
		""" Show dialog and change task start date.

		Args:
			parent_wnd: parent wx window
			task: task to modify
		Returns:
			True if date was changed.
		"""
		return cls._set_date(parent_wnd, task, 'start_date', 'start_time_set')

	@classmethod
	def task_change_remind(cls, parent_wnd, task):
		""" Show dialog and change task start date.

		Args:
			parent_wnd: parent wx window
			task: task to modify
		Returns:
			True if date was changed.
		"""
		alarm = None
		if task.alarm:
			alarm = DTU.datetime2timestamp(task.alarm)
		dlg = DlgRemindSettings(parent_wnd, alarm, task.alarm_pattern)
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

	@classmethod
	def task_change_hide_until(cls, parent_wnd, task):
		""" Show dialog and change task show settings.

		Args:
			parent_wnd: parent wx window
			task: task to modify
		Returns:
			True if date was changed.
		"""
		date_time = None
		if task.hide_until:
			date_time = DTU.datetime2timestamp(task.hide_until)
		dlg = DlgShowSettings(parent_wnd, date_time, task.hide_pattern)
		if dlg.run(True):
			if dlg.datetime:
				task.hide_until = DTU.timestamp2datetime(dlg.datetime)
			else:
				task.hide_until = None
			task.hide_pattern = dlg.pattern
			task_logic.update_task_hide(task)
			return True
		return False

	@classmethod
	def task_change_tags(cls, parent_wnd, task, session):
		""" Show dialog and change task's tags.

		Args:
			parent_wnd: parent wx window
			task: task to modify
			session: current SqlAlchemy session
		Returns:
			True if tags was changed.
		"""
		tags_uuids = [tasktag.tag_uuid for tasktag in task.tags]
		dlg = DlgSelectTags(parent_wnd, tags_uuids)
		if dlg.run(True):
			new_tags = dlg.selected_tags
			for tasktag in list(task.tags):
				if tasktag.tag_uuid not in new_tags:
					task.tags.delete(tasktag)  # pylint: disable=E1103
				else:
					new_tags.remove(tasktag.tag_uuid)
			for tag_uuid in new_tags:
				tasktag = OBJ.TaskTag()
				tasktag.tag = session.query(  # pylint: disable=E1101
						OBJ.Tag).filter_by(uuid=tag_uuid).first()
				task.tags.append(tasktag)  # pylint: disable=E1103
			return True
		return False

	@classmethod
	def task_change_repeat(cls, parent_wnd, task):
		""" Show dialog and change task's repeat settings.

		Args:
			parent_wnd: parent wx window
			task: task to modify
		Returns:
			True if task was changed.
		"""
		dlg = DlgRepeatSettings(parent_wnd, task.repeat_pattern, task.repeat_from)
		if dlg.run(True):
			task.repeat_from = dlg.repeat_from
			task.repeat_pattern = dlg.pattern
			return True
		return False

	@classmethod
	def _set_date(cls, parent_wnd, task, attr_date, attr_time_set):
		""" Wyśweitlenie dlg wyboru daty dla danego atrybutu """
		value = getattr(task, attr_date)
		if value:
			value = DTU.datetime2timestamp(value)
		dlg = DlgDateTime(parent_wnd, value, getattr(task, attr_time_set))
		if dlg.run(True):
			date = None
			if dlg.timestamp:
				date = DTU.timestamp2datetime(dlg.timestamp)
			setattr(task, attr_date, date)
			setattr(task, attr_time_set, dlg.is_time_set)
			return True
		return False
