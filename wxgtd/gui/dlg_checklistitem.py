# -*- coding: utf-8 -*-

"""
Klasa dialogu edycji elementu check listy
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2013"
__version__ = "2010-11-25"

import logging
import datetime
import gettext

import wx
try:
	from wx.lib.pubsub.pub import Publisher
except ImportError:
	from wx.lib.pubsub import Publisher

from wxgtd.model import objects as OBJ
from wxgtd.model import enums
from wxgtd.wxtools.validators import Validator, ValidatorDv
from wxgtd.wxtools.validators import v_length as LVALID

from _base_dialog import BaseDialog
import _fmt as fmt

_ = gettext.gettext
_LOG = logging.getLogger(__name__)


class DlgChecklistitem(BaseDialog):
	"""
	Dlg edycji elementów listy.
	WARRNING: okienko niemodalne; obsługa zapisywania tutaj
	"""

	def __init__(self, parent, task_uuid, parent_uuid=None):
		BaseDialog.__init__(self, parent, 'dlg_checklistitem')
		self._setup_comboboxes()
		self._setup(task_uuid, parent_uuid)
		self._refresh_static_texts()

	def _load_controls(self, wnd):
		BaseDialog._load_controls(self, wnd)

	def _create_bindings(self):
		BaseDialog._create_bindings(self)
		self['lb_notes_list'].Bind(wx.EVT_LISTBOX, self._on_lb_notes_list)
		self._wnd.Bind(wx.EVT_BUTTON, self._on_btn_new_note, id=wx.ID_ADD)
		self['btn_del_note'].Bind(wx.EVT_BUTTON, self._on_btn_del_note)
		self['btn_save_note'].Bind(wx.EVT_BUTTON, self._on_btn_save_note)

	def _setup(self, task_uuid, parent_uuid):
		_LOG.debug("DlgTask(%r)", task_uuid)
		self._current_note = None
		self._session = OBJ.Session()
		if task_uuid:
			self._task = self._session.query(OBJ.Task).filter_by(
					uuid=task_uuid).first()
		else:
			self._task = OBJ.Task(type=enums.TYPE_CHECKLIST_ITEM,
					parent_uuid=parent_uuid)
			self._session.add(self._task)
		task = self._task
		self._data = {'prev_completed': task.completed}
		self['tc_title'].SetValidator(Validator(task, 'title',
				validators=LVALID.NotEmptyValidator(), field='title'))
		self['tc_note'].SetValidator(Validator(task, 'note',))
		self['cb_checklist'].SetValidator(ValidatorDv(task, 'parent_uuid'))
		self['l_created'].SetLabel(str(task.created))
		self['l_modified'].SetLabel(str(task.modified))
		self['cb_completed'].SetValidator(Validator(task, 'task_completed'))
		self['cb_starred'].SetValidator(Validator(task, 'starred'))

	def _setup_comboboxes(self):
		cb_checklist = self['cb_checklist']
		for checklist in OBJ.Task.all_checklists():
			cb_checklist.Append(checklist.title, checklist.uuid)

	def _on_save(self, evt):
		if not self._wnd.Validate():
			return
		if not self._wnd.TransferDataFromWindow():
			return
		self._session.commit()
		Publisher.sendMessage('task.update', data={'task_uuid': self._task.uuid})
		self._on_ok(evt)

	def _on_lb_notes_list(self, evt):
		note_uuid = evt.GetClientData()
		for note in self._task.notes:
			if note.uuid == note_uuid:
				# czy aktualne jest zmienione
				if note != self._current_note and self._current_note:
					# TODO: potwierdzenie zapisania
					value = self['tc_notes_note'].GetValue()
					if value != self._current_note.title:
						self._current_note.title = value
				self._current_note = note
				self['tc_notes_note'].SetValue(note.title or '')

	def _on_btn_new_note(self, _evt):
		self._save_current_note()
		self._current_note = OBJ.Tasknote(title=_("New note"))
		self['tc_notes_note'].SetValue(self._current_note.title)

	def _on_btn_del_note(self, _evt):
		lb_notes_list = self['lb_notes_list']
		sel = lb_notes_list.GetSelection()
		if sel < 0:
			return
		del self._task.notes[sel]
		self._refresh_static_texts()

	def _on_btn_save_note(self, _evt):
		self._save_current_note()

	def _save_current_note(self):
		cnote = self._current_note
		if cnote:
			value = self['tc_notes_note'].GetValue()
			if value and value != cnote.title:
				cnote.title = value
				cnote.modified = datetime.datetime.now()
				if not cnote.created:
					cnote.created = cnote.modified
					self._task.notes.append(cnote)
			wx.CallAfter(self._refresh_static_texts)

	def _refresh_static_texts(self):
		""" Odświeżenie pól dat na dlg """
		task = self._task
		lb_notes_list = self['lb_notes_list']
		lb_notes_list.Clear()
		for note in task.notes:
			lb_notes_list.Append(note.title[:50], note.uuid)
		if task.completed:
			self['l_completed_date'].SetLabel(fmt.format_timestamp(task.completed,
					True))
		else:
			self['l_completed_date'].SetLabel('')
