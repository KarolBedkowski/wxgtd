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

from wxgtd.model import objects as OBJ
from wxgtd.model import enums
from wxgtd.wxtools.validators import Validator, ValidatorDv

from ._base_task_dialog import BaseTaskDialog
from . import _fmt as fmt

_ = gettext.gettext
_LOG = logging.getLogger(__name__)


class DlgTask(BaseTaskDialog):
	""" Edit task dialog.

	WARRNING: non-modal dialog

	Args:
		parent: parent windows.
		task: task to edit.
		session: SqlAlchemy session.
		controller: TaskDialogControler associated to task.
	"""

	def __init__(self, parent, task, session, controller):
		BaseTaskDialog.__init__(self, parent, 'dlg_task', task, session,
				controller)

	def _create_bindings(self, wnd):
		BaseTaskDialog._create_bindings(self, wnd)
		self['btn_due_date_set'].Bind(wx.EVT_BUTTON, self._on_btn_due_date_set)
		self['btn_start_date_set'].Bind(wx.EVT_BUTTON, self._on_btn_start_date_set)
		self['btn_remind_set'].Bind(wx.EVT_BUTTON, self._on_btn_remiand_set)
		self['btn_hide_until_set'].Bind(wx.EVT_BUTTON, self._on_btn_hide_until_set)
		self['btn_repeat_set'].Bind(wx.EVT_BUTTON, self._on_btn_repeat_set)
		self['btn_select_tags'].Bind(wx.EVT_BUTTON, self._on_btn_select_tags)
		self['btn_change_type'].Bind(wx.EVT_BUTTON, self._on_btn_change_type)
		self['sl_priority'].Bind(wx.EVT_SCROLL, self._on_sl_priority)

	def _setup(self, task):
		_LOG.debug("DlgTask(%r)", task.uuid)
		BaseTaskDialog._setup(self, task)
		self[wx.ID_DELETE].Enable(bool(task.uuid))
		self._data['duration_d'] = self._data['duration_h'] = \
				self._data['duration_m'] = 0
		if task.duration:
			duration = task.duration
			self._data['duration_d'] = int(duration / 1440)
			duration = duration % 1440
			self._data['duration_h'] = int(duration / 60)
			self._data['duration_m'] = duration % 60
		self['cb_status'].SetValidator(ValidatorDv(task, 'status'))
		self['cb_context'].SetValidator(ValidatorDv(task, 'context_uuid'))
		self['cb_folder'].SetValidator(ValidatorDv(task, 'folder_uuid'))
		self['cb_goal'].SetValidator(ValidatorDv(task, 'goal_uuid'))
		self['sl_priority'].SetValidator(Validator(task, 'priority'))
		self['sc_duration_d'].SetValidator(Validator(self._data, 'duration_d'))
		self['sc_duration_h'].SetValidator(Validator(self._data, 'duration_h'))
		self['sc_duration_m'].SetValidator(Validator(self._data, 'duration_m'))

	def _setup_comboboxes(self):
		BaseTaskDialog._setup_comboboxes(self)
		cb_status = self['cb_status']
		cb_status.Clear()
		for key, status in sorted(enums.STATUSES.iteritems()):
			cb_status.Append(status, key)
		cb_context = self['cb_context']
		cb_context.Clear()
		for context in OBJ.Context.all():
			cb_context.Append(context.title, context.uuid)
		cb_folder = self['cb_folder']
		cb_folder.Clear()
		for folder in OBJ.Folder.all():
			cb_folder.Append(folder.title, folder.uuid)
		cb_goal = self['cb_goal']
		cb_goal.Clear()
		for goal in OBJ.Goal.all():
			cb_goal.Append(goal.title, goal.uuid)

	def _transfer_data_from_window(self):
		self._task.duration = self._data['duration_d'] * 1440 + \
				self._data['duration_h'] * 60 + self._data['duration_m']
		return BaseTaskDialog._transfer_data_from_window(self)

	def _on_btn_due_date_set(self, _evt):
		if self._controller.task_change_due_date():
			self._refresh_static_texts()

	def _on_btn_start_date_set(self, _evt):
		if self._controller.task_change_start_date():
			self._refresh_static_texts()

	def _on_btn_remiand_set(self, _evt):
		if self._controller.task_change_remind():
			self._refresh_static_texts()

	def _on_btn_hide_until_set(self, _evt):
		if self._controller.task_change_hide_until():
			self._refresh_static_texts()

	def _on_btn_repeat_set(self, _evt):
		if self._controller.task_change_repeat():
			self._refresh_static_texts()

	def _on_btn_select_tags(self, _evt):
		if self._controller.task_change_tags():
			self._refresh_static_texts()

	def _on_btn_change_type(self, _evt):
		parent_type = self._task.parent.type if self._task.parent else None
		if parent_type == enums.TYPE_CHECKLIST:
			# nie można zmienić typu z TYPE_CHECKLIST_ITEM
			self._task.type = enums.TYPE_CHECKLIST_ITEM
			return
		values = [enums.TYPE_TASK, enums.TYPE_CALL, enums.TYPE_EMAIL,
				enums.TYPE_SMS, enums.TYPE_RETURN_CALL, enums.TYPE_PROJECT,
				enums.TYPE_CHECKLIST]
		choices = [enums.TYPES[val] for val in values]
		dlg = wx.SingleChoiceDialog(self.wnd, _("Change task type to:"),
				_("Task"), choices, wx.CHOICEDLG_STYLE)
		if dlg.ShowModal() == wx.ID_OK:
			self._task.type = values[dlg.GetSelection()]
			self._refresh_static_texts()
			self._on_task_type_change()
		dlg.Destroy()

	def _on_sl_priority(self, _evt):
		self['l_prio'].SetLabel(enums.PRIORITIES[self['sl_priority'].GetValue()])

	def _refresh_static_texts(self):
		""" Odświeżenie pól dat na dlg """
		BaseTaskDialog._refresh_static_texts(self)
		task = self._task
		due_date = (task.due_date_project if task.type == enums.TYPE_PROJECT
				else task.due_date)
		self['l_due'].SetLabel(fmt.format_timestamp(due_date, task.due_time_set))
		self['l_start_date'].SetLabel(fmt.format_timestamp(task.start_date,
				task.start_time_set))
		self['l_tags'].SetLabel(", ".join(tag.tag.title for tag in task.tags) or '')
		if task.alarm_pattern:
			self['l_remind'].SetLabel(enums.REMIND_PATTERNS[task.alarm_pattern])
		elif task.alarm:
			self['l_remind'].SetLabel(fmt.format_timestamp(task.alarm, True))
		else:
			self['l_remind'].SetLabel('')
		if task.hide_pattern and task.hide_pattern != 'given date':
			self['l_hide_until'].SetLabel(enums.HIDE_PATTERNS[task.hide_pattern])
		elif task.hide_until:
			self['l_hide_until'].SetLabel(fmt.format_timestamp(task.hide_until,
					True))
		else:
			self['l_hide_until'].SetLabel('')
		self['l_repeat'].SetLabel(enums.REPEAT_PATTERN.get(task.repeat_pattern,
				task.repeat_pattern or ""))
		self['l_prio'].SetLabel(enums.PRIORITIES[task.priority])
		self['l_type'].SetLabel(enums.TYPES[task.type or enums.TYPE_TASK])
		self['btn_change_type'].Enable(task.type != enums.TYPE_CHECKLIST_ITEM)
