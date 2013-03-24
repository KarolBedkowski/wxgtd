# -*- coding: utf-8 -*-

"""
Klasa bazowa dla wszystkich dlg.
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2010-2013"
__version__ = "2010-11-25"


import wx
try:
	from wx.lib.pubsub.pub import Publisher
except ImportError:
	from wx.lib.pubsub import Publisher

from wxgtd.model import objects as OBJ
from wxgtd.wxtools import validators
from wxgtd.wxtools.validators import length as LVALID

from _base_dialog import BaseDialog


class DlgTask(BaseDialog):
	"""
	Dlg edycji zadań.
	WARRNING: okienko niemodalne; obsługa zapisywania tutaj
	"""

	def __init__(self, parent, task):
		BaseDialog.__init__(self, parent, 'dlg_task')
		self._setup_comboboxes()
		self._setup(task)

	def _load_controls(self, wnd):
		BaseDialog._load_controls(self, wnd)
		wnd.SetExtraStyle(wx.WS_EX_VALIDATE_RECURSIVELY)

	def _create_bindings(self):
		BaseDialog._create_bindings(self)

	def _setup(self, task):
		self._task = task
		self['tc_title'].SetValidator(validators.Validator(task, 'title',
				validators=LVALID.NotEmptyValidator(), field='title'))
		self['cb_stared'].SetValidator(validators.Validator(task, 'starred'))
		self['cb_status'].SetValidator(validators.ValidatorDv(task, 'status'))
		self['cb_context'].SetValidator(validators.ValidatorDv(task, 'context_uuid'))
		self['cb_folder'].SetValidator(validators.ValidatorDv(task, 'folder_uuid'))
		self['cb_goal'].SetValidator(validators.ValidatorDv(task, 'goal_uuid'))
		self['cb_type'].SetValidator(validators.ValidatorDv(task, 'type'))

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

	def _on_save(self, evt):
		if not self._wnd.Validate():
			return
		if not self._wnd.TransferDataFromWindow():
			return
		self._task.save_or_update()
		self._task.connection.commit()
		Publisher.sendMessage('task.update', data={'task_uuid': self._task.uuid})
		self._on_ok(evt)
