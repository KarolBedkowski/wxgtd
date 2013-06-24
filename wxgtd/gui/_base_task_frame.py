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
from wxgtd.wxtools import wxutils
from wxgtd.lib import fmt

from ._base_frame import BaseFrame
from . import dialogs
from . import message_boxes as mbox
from .dlg_projects_tree import DlgProjectTree

_ = gettext.gettext
_LOG = logging.getLogger(__name__)


class BaseTaskFrame(BaseFrame):
	""" Base class for all task dialogs.

	Args:
		parent: parent windows.
		task: task to edit.
		session: SqlAlchemy session.
		controller: TaskController associated to task.
	"""

	_xrc_resource = "wxgtd.xrc"

	def __init__(self, parent, task, session, controller):
		BaseFrame.__init__(self, parent)
		self._session = session
		self._task = task
		self._controller = controller
		self._setup_comboboxes()
		self._setup(task)
		self._refresh_static_texts()
		self._post_create()

	def run(self, _dummy=False):
		""" Run (show) dialog.  """
		self.wnd.Show()
		self.wnd.Raise()

	def close(self):
		self.wnd.Destroy()

	def _create_bindings(self, wnd):
		BaseFrame._create_bindings(self, wnd)
		self['lb_notes_list'].Bind(wx.EVT_LISTBOX_DCLICK, self._on_lb_notes_list)
		wnd.Bind(wx.EVT_BUTTON, self._on_btn_delete, id=wx.ID_DELETE)
		wnd.Bind(wx.EVT_BUTTON, self._on_btn_new_note, id=wx.ID_ADD)
		wnd.Bind(wx.EVT_BUTTON, self._on_save, id=wx.ID_SAVE)
		wnd.Bind(wx.EVT_BUTTON, self._on_ok, id=wx.ID_OK)
		wnd.Bind(wx.EVT_BUTTON, self._on_cancel, id=wx.ID_CLOSE)
		self['btn_del_note'].Bind(wx.EVT_BUTTON, self._on_btn_del_note)
		self['btn_change_project'].Bind(wx.EVT_BUTTON,
				self._on_btn_change_project)

	def _setup(self, task):
		_LOG.debug("BaseTaskFrame.setup(%r)", task.uuid)
		self._original_task = task.clone(cleanup=False)
		self._data = {'prev_completed': task.completed}
		self['tc_title'].SetValidator(Validator(task, 'title',
				validators=LVALID.NotEmptyValidator(), field='title'))
		self['tc_note'].SetValidator(Validator(task, 'note',))
		self['l_created'].SetLabel(fmt.format_timestamp(task.created))
		self['l_modified'].SetLabel(fmt.format_timestamp(task.modified))
		self['cb_completed'].SetValidator(Validator(task, 'task_completed'))
		self['cb_starred'].SetValidator(Validator(task, 'starred'))
		self['tc_note'].Bind(wx.EVT_TEXT_URL, self._on_text_url)
		self['tc_title'].Bind(wx.EVT_TEXT_URL, self._on_text_url)

	def _setup_comboboxes(self):  # pylint: disable=R0201
		pass

	def _on_save(self, evt):
		if not self._validate():
			return
		if not self._transfer_data_from_window():
			return
		if not self._data['prev_completed'] and self._task.completed:
			# zakonczono zadanie
			if not self._controller.confirm_set_task_complete():
				return
			if not task_logic.complete_task(self._task, self._session):
				return
		task_logic.save_modified_task(self._task, self._session)
		self._on_ok(evt)

	def _on_cancel(self, _evt):
		if self._data_changed() and not self._confirm_close():
			_LOG.debug('data changed')
			return
		self._session.rollback()
		self.wnd.Close()

	def _on_close(self, evt):
		self._controller.close()
		BaseFrame._on_close(self, evt)

	def _on_ok(self, _evt):
		""" Action for ok/yes - close window. """
		self.wnd.Close()

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
			if self._controller.task_change_parent(parent_uuid):
				self._refresh_static_texts()
				self._on_task_type_change()

	def _on_btn_delete(self, _evt):
		tuuid = self._task.uuid
		if tuuid and self._controller.delete_task():
			self._on_ok(None)

	def _on_text_url(self, evt):  # pylint: disable=R0201
		""" Double click on url-s open browser. """
		if not evt.GetMouseEvent().ButtonDClick(wx.MOUSE_BTN_LEFT):
			return
		start, end = evt.GetURLStart(), evt.GetURLEnd()
		url = evt.GetEventObject().GetValue()[start:end]
		_LOG.debug("BaseTaskFrame._on_text_url: open url=%r", url)
		wx.LaunchDefaultBrowser(url)

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
		if not self._transfer_data_from_window():
			return False
		return not self._original_task.compare(self._task)

	def _validate(self):
		""" Validate values entered in dialog.

		Returns:
			True = no error.
		"""
		return self.wnd.Validate()

	def _transfer_data_from_window(self):
		""" Transfer values from widgets to objects.

		Returns:
			True = no error.
		"""
		try:
			return self.wnd.TransferDataFromWindow()
		finally:
			pass
		return False

	def _confirm_close(self):
		res = mbox.message_box_not_save_confirm(self.wnd, None)
		if res == wx.ID_NO:
			return True
		if res == wx.ID_YES:
			self._on_save(None)
		return False

	@wxutils.call_after
	def _on_task_type_change(self):
		""" Called after task type change. """
		fake_title = False
		if not self['tc_title'].GetValue().strip():
			self['tc_title'].SetValue("<?>")
			fake_title = True
		self._transfer_data_from_window()
		if fake_title:
			self._task.title = ""
			self['tc_title'].SetValue("")
		self._controller.change_task_type()

	@wxutils.call_after
	def _post_create(self):
		self.wnd.TransferDataToWindow()
		self['tc_title'].SetFocus()
