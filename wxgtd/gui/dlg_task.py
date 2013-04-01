# -*- coding: utf-8 -*-

"""
Klasa bazowa dla wszystkich dlg.
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2010-2013"
__version__ = "2010-11-25"

import time
import logging

import wx
try:
	from wx.lib.pubsub.pub import Publisher
except ImportError:
	from wx.lib.pubsub import Publisher

from wxgtd.model import objects as OBJ
from wxgtd.wxtools.validators import Validator, ValidatorDv
from wxgtd.wxtools.validators import v_length as LVALID

from _base_dialog import BaseDialog
from dlg_datetime import DlgDateTime

_LOG = logging.getLogger(__name__)


class DlgTask(BaseDialog):
	"""
	Dlg edycji zadań.
	WARRNING: okienko niemodalne; obsługa zapisywania tutaj
	"""

	def __init__(self, parent, task):
		BaseDialog.__init__(self, parent, 'dlg_task')
		self._setup_comboboxes()
		self._setup(task)
		self._refresh_dates()

	def _load_controls(self, wnd):
		BaseDialog._load_controls(self, wnd)

	def _create_bindings(self):
		BaseDialog._create_bindings(self)
		self['btn_due_date_set'].Bind(wx.EVT_BUTTON, self._on_btn_due_date_set)
		self['btn_start_date_set'].Bind(wx.EVT_BUTTON, self._on_btn_start_date_set)

	def _setup(self, task):
		_LOG.debug("DlgTask(%r)", task)
		self._task = task
		self._dates = {}
		self._dates['due_time'] = self._dates['due_date'] = task.due_date
		self._dates['start_time'] = self._dates['start_date'] = task.start_date
		self['tc_title'].SetValidator(Validator(task, 'title',
				validators=LVALID.NotEmptyValidator(), field='title'))
		self['tc_note'].SetValidator(Validator(task, 'note',))
		self['cb_status'].SetValidator(ValidatorDv(task, 'status'))
		self['cb_context'].SetValidator(ValidatorDv(task, 'context_uuid'))
		self['cb_folder'].SetValidator(ValidatorDv(task, 'folder_uuid'))
		self['cb_goal'].SetValidator(ValidatorDv(task, 'goal_uuid'))
		self['cb_type'].SetValidator(ValidatorDv(task, 'type'))
		# parent == projekt/lista
		self['cb_project'].SetValidator(ValidatorDv(task,
				'parent_uuid'))
		self['l_created'].SetLabel(str(time.asctime(time.localtime(task.created))))
		self['l_modified'].SetLabel(str(time.asctime(time.localtime(task.modified))))
		self['cb_completed'].SetValidator(Validator(task, 'task_completed'))
		self['cb_starred'].SetValidator(Validator(task, 'starred'))
		self['sl_priority'].SetValidator(Validator(task, 'priority'))

	def _setup_comboboxes(self):
		cb_status = self['cb_status']
		for key, status in sorted(OBJ.STATUSES.iteritems()):
			cb_status.Append(status, key)
		cb_types = self['cb_type']
		for key, typename in sorted(OBJ.TYPES.iteritems()):
			cb_types.Append(typename, key)
		cb_context = self['cb_context']
		for context in OBJ.Context.all():
			cb_context.Append(context.title, context.uuid)
		cb_folder = self['cb_folder']
		for folder in OBJ.Folder.all():
			cb_folder.Append(folder.title, folder.uuid)
		cb_goal = self['cb_goal']
		for goal in OBJ.Goal.all():
			cb_goal.Append(goal.title, goal.uuid)
		cb_project = self['cb_project']
		for project in OBJ.Task.all_projects():
			# projects
			cb_project.Append(project.title, project.uuid)

	def _on_save(self, evt):
		if not self._wnd.Validate():
			return
		if not self._wnd.TransferDataFromWindow():
			return
		self._task.save_or_update()
		self._task.connection.commit()
		Publisher.sendMessage('task.update', data={'task_uuid': self._task.uuid})
		self._on_ok(evt)

	def _on_btn_due_date_set(self, _evt):
		self._set_date('due_date', 'due_time_set')

	def _on_btn_start_date_set(self, _evt):
		self._set_date('start_date', 'start_time_set')

	def _refresh_dates(self):
		""" Odświeżenie pól dat na dlg """
		task = self._task
		self['l_due'].SetLabel(format_timestamp(task.due_date,
				task.due_time_set))
		self['l_start_date'].SetLabel(format_timestamp(task.start_date,
				task.start_time_set))

	def _set_date(self, attr_date, attr_time_set):
		""" Wyśweitlenie dlg wyboru daty dla danego atrybutu """
		dlg = DlgDateTime(self._wnd, getattr(self._task, attr_date),
				getattr(self._task, attr_time_set))
		if dlg.run(True):
			setattr(self._task, attr_date, dlg.timestamp)
			setattr(self._task, attr_time_set, dlg.is_time_set)
			self._refresh_dates()


def format_timestamp(timestamp, show_time):
	if not timestamp:
		return ""
	if show_time:
		return time.strftime("%x %X", time.localtime(timestamp))
	return time.strftime("%x", time.localtime(timestamp))
