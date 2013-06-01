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
from wxgtd.logic import task as task_logic
from wxgtd.lib import datetimeutils as DTU
from wxgtd.wxtools.validators import Validator, ValidatorDv

from ._base_task_dialog import BaseTaskDialog
from .dlg_datetime import DlgDateTime
from .dlg_remind_settings import DlgRemindSettings
from .dlg_show_settings import DlgShowSettings
from .dlg_repeat_settings import DlgRepeatSettings
from .dlg_select_tags import DlgSelectTags
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
		if self._task.type == enums.TYPE_PROJECT:
			self._set_date('due_date_project', 'due_time_set')
		else:
			self._set_date('due_date', 'due_time_set')

	def _on_btn_start_date_set(self, _evt):
		self._set_date('start_date', 'start_time_set')

	def _on_btn_remiand_set(self, _evt):
		task = self._task
		alarm = None
		if task.alarm:
			alarm = DTU.datetime2timestamp(task.alarm)
		dlg = DlgRemindSettings(self._wnd, alarm, task.alarm_pattern)
		if dlg.run(True):
			if dlg.alarm:
				task.alarm = DTU.timestamp2datetime(dlg.alarm)
				task.alarm_pattern = None
			else:
				task.alarm = None
				task.alarm_pattern = dlg.alarm_pattern
			task_logic.update_task_alarm(task)
			self._refresh_static_texts()

	def _on_btn_hide_until_set(self, _evt):
		task = self._task
		date_time = None
		if task.hide_until:
			date_time = DTU.datetime2timestamp(task.hide_until)
		dlg = DlgShowSettings(self._wnd, date_time, task.hide_pattern)
		if dlg.run(True):
			if dlg.datetime:
				task.hide_until = DTU.timestamp2datetime(dlg.datetime)
			else:
				task.hide_until = None
			task.hide_pattern = dlg.pattern
			task_logic.update_task_hide(task)
			self._refresh_static_texts()

	def _on_btn_repeat_set(self, _evt):
		task = self._task
		dlg = DlgRepeatSettings(self._wnd, task.repeat_pattern, task.repeat_from)
		if dlg.run(True):
			task.repeat_from = dlg.repeat_from
			task.repeat_pattern = dlg.pattern
			self._refresh_static_texts()

	def _on_btn_select_tags(self, _evt):
		task = self._task
		tags_uuids = [tasktag.tag_uuid for tasktag in task.tags]
		dlg = DlgSelectTags(self._wnd, tags_uuids)
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

	def _set_date(self, attr_date, attr_time_set):
		""" Wyśweitlenie dlg wyboru daty dla danego atrybutu """
		value = getattr(self._task, attr_date)
		if value:
			value = DTU.datetime2timestamp(value)
		dlg = DlgDateTime(self._wnd, value,
				getattr(self._task, attr_time_set))
		if dlg.run(True):
			date = None
			if dlg.timestamp:
				date = DTU.timestamp2datetime(dlg.timestamp)
			setattr(self._task, attr_date, date)
			setattr(self._task, attr_time_set, dlg.is_time_set)
			self._refresh_static_texts()
