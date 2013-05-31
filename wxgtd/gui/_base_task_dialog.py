# -*- coding: utf-8 -*-

"""Base class for all task dialog classes.

Copyright (c) Karol Będkowski, 2013

This file is part of wxGTD
Licence: GPLv2+
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2013"
__version__ = "2013-05-19"

import logging
import gettext

import wx

from wxgtd.model import objects as OBJ
from wxgtd.logic import task as task_logic
from wxgtd.wxtools.validators import Validator
from wxgtd.wxtools.validators import v_length as LVALID

from ._base_dialog import BaseDialog
from . import _fmt as fmt
from . import dialogs
from . import message_boxes as mbox
from .dlg_projects_tree import DlgProjectTree

_ = gettext.gettext
_LOG = logging.getLogger(__name__)


class BaseTaskDialog(BaseDialog):
	""" Base class for all task dialogs.

	Args:
		parent: parent window
		dialog_name: name of dialog in xrc file
		task_uuid: uuid task for edit; if empty - create new task
		parent_uuid: optional parent task uuid.
	"""

	def __init__(self, parent, dialog_name, task_uuid, parent_uuid=None):
		BaseDialog.__init__(self, parent, dialog_name)
		self._setup_comboboxes()
		self._setup(task_uuid, parent_uuid)
		self._refresh_static_texts()

	def _create_bindings(self, wnd):
		BaseDialog._create_bindings(self, wnd)
		self['lb_notes_list'].Bind(wx.EVT_LISTBOX_DCLICK, self._on_lb_notes_list)
		wnd.Bind(wx.EVT_BUTTON, self._on_btn_delete, id=wx.ID_DELETE)
		wnd.Bind(wx.EVT_BUTTON, self._on_btn_new_note, id=wx.ID_ADD)
		self['btn_del_note'].Bind(wx.EVT_BUTTON, self._on_btn_del_note)
		self['btn_change_project'].Bind(wx.EVT_BUTTON,
				self._on_btn_change_project)

	def _setup(self, task_uuid, parent_uuid):
		_LOG.debug("BaseTaskDialog.setup(%r, %r)", task_uuid, parent_uuid)
		self._session = OBJ.Session()
		if task_uuid:
			self._task = self._load_task(task_uuid)
		else:
			self._task = self._create_task(parent_uuid)
			self._session.add(self._task)  # pylint: disable=E1101
		task = self._task
		self._original_task = task.clone(cleanup=False)
		self._data = {'prev_completed': task.completed}
		self['tc_title'].SetValidator(Validator(task, 'title',
				validators=LVALID.NotEmptyValidator(), field='title'))
		self['tc_note'].SetValidator(Validator(task, 'note',))
		self['l_created'].SetLabel(fmt.format_timestamp(task.created))
		self['l_modified'].SetLabel(fmt.format_timestamp(task.modified))
		self['cb_completed'].SetValidator(Validator(task, 'task_completed'))
		self['cb_starred'].SetValidator(Validator(task, 'starred'))

	def _setup_comboboxes(self):  # pylint: disable=R0201
		pass

	def _load_task(self, _task_uuid):  # pylint: disable=R0201
		return None

	def _create_task(self, _parent_uuid):  # pylint: disable=R0201
		return None

	def _on_save(self, evt):
		if not self._wnd.Validate():
			return
		if not self._wnd.TransferDataFromWindow():
			return
		task_logic.save_modified_task(self._task, self._session)
		self._on_ok(evt)

	def _on_cancel(self, _evt):
		if self._data_changed() and not self._confirm_close():
			_LOG.debug('data changed')
			return
		self._session.rollback()
		self._wnd.Close()

	def _on_close(self, evt):
		self._session.close()
		BaseDialog._on_close(self, evt)

	def _on_lb_notes_list(self, _evt):
		sel = self['lb_notes_list'].GetSelection()
		if sel < 0:
			return
		note = self._task.notes[sel]
		dlg = dialogs.MultilineTextDialog(self.wnd, note.title,
				_("Task Note"), buttons=wx.ID_SAVE | wx.ID_CLOSE)
		if dlg.ShowModal() == wx.ID_SAVE:
			note.title = dlg.text
			self._session.add(note)
		dlg.Destroy()
		self._refresh_static_texts()

	def _on_btn_new_note(self, _evt):
		note = OBJ.Tasknote()
		dlg = dialogs.MultilineTextDialog(self.wnd, note.title,
				_("Task Note"), buttons=wx.ID_SAVE | wx.ID_CLOSE)
		if dlg.ShowModal() == wx.ID_SAVE:
			note.title = dlg.text
			self._session.add(note)
			self._task.notes.append(note)
		dlg.Destroy()
		self._refresh_static_texts()

	def _on_btn_del_note(self, _evt):
		lb_notes_list = self['lb_notes_list']
		sel = lb_notes_list.GetSelection()
		if sel < 0:
			return
		if not mbox.message_box_delete_confirm(self.wnd, _("note")):
			return
		note = self._task.notes[sel]
		if note.uuid:
			self._session.delete(note)
		del self._task.notes[sel]
		self._refresh_static_texts()

	def _on_btn_change_project(self, _evt):
		dlg = DlgProjectTree(self.wnd)
		if dlg.run(modal=True):
			parent_uuid = dlg.selected
			if task_logic.change_task_parent(self._task, parent_uuid,
					self._session, self.wnd):
				self._refresh_static_texts()

	def _on_btn_delete(self, _evt):
		tuuid = self._task.uuid
		if tuuid:
			if task_logic.delete_task(tuuid, self.wnd, self._session):
				self._on_ok(None)

	def _refresh_static_texts(self):
		""" Odświeżenie pól dat na dlg """
		task = self._task
		lb_notes_list = self['lb_notes_list']
		lb_notes_list.Clear()
		for note in task.notes:
			lb_notes_list.Append(note.title[:50], note.uuid)
		self['l_project'].SetLabel(task.parent.title if task.parent else '')
		if task.completed:
			self['l_completed_date'].SetLabel(fmt.format_timestamp(task.completed,
					True))
		else:
			self['l_completed_date'].SetLabel('')

	def _data_changed(self):
		if not self._wnd.TransferDataFromWindow():
			return False
		return not self._original_task.compare(self._task)
