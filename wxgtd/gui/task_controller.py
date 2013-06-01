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
from wxgtd.model import objects as OBJ
from wxgtd.model import enums
from wxgtd.logic import task as task_logic

from .dlg_task import DlgTask
from .dlg_checklistitem import DlgChecklistitem

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
