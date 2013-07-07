# -*- coding: utf-8 -*-

""" Base class for dialogs that manage application dictionaries.

Copyright (c) Karol Będkowski, 2013

This file is part of wxGTD
Licence: GPLv2+
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2013"
__version__ = "2013-04-27"

import gettext
import logging
import datetime

import wx
try:
	from wx.lib.pubsub.pub import Publisher
except ImportError:
	from wx.lib.pubsub import Publisher  # pylint: disable=E0611

from wxgtd.model.objects import Session
from wxgtd.wxtools.validators import Validator, ValidatorColorStr
from wxgtd.gui._base_dialog import BaseDialog
from wxgtd.gui import message_boxes as mbox
from wxgtd.gui.dlg_trash import DlgTrash

_LOG = logging.getLogger(__name__)
_ = gettext.gettext


class DictBaseDlg(BaseDialog):
	""" Base class for dialogs that manage application dictionaries stored
	in class managed by SqlAlchemy.

	Args:
		parent: parent window
		dlg_name: name of dialog in resource file
	"""

	_items_list_control = "lb_items"  # nazwa widgeta zawierającego listę
			# elementów
	_item_name = ""  # nazwa elementu
	_item_class = None  # klasa obiektów

	def __init__(self, parent, dlg_name):
		self._displayed_item = None  # aktualnie wuświetlany obiekt

		class _Proxy(object):
			""" Proxy class that allow use validators on dynamically changed
			objects. """
			# pylint: disable=W0212, E0213, R0903
			def __getattr__(selfi, key):
				if not self._displayed_item:
					return ""
				return getattr(self._displayed_item, key)

			def __setattr__(selfi, key, val):
				setattr(self._displayed_item, key, val)

		self._proxy = _Proxy()
		self._current_selected_uuid = None
		self._session = Session()
		self._items_lctrl = None
		BaseDialog.__init__(self, parent, dlg_name, save_pos=False)
		wx.CallAfter(self._refresh_list)

	def _load_controls(self, wnd):
		BaseDialog._load_controls(self, wnd)
		self._items_lctrl = self[self._items_list_control]
		self['tc_title'].SetValidator(Validator(self._proxy, 'title'))
		self['tc_note'].SetValidator(Validator(self._proxy, 'note'))
		self['colorselect'].SetValidator(ValidatorColorStr(self._proxy,
				'bg_color', with_alpha=True))

	def _create_bindings(self, wnd):
		BaseDialog._create_bindings(self, wnd)
		wnd.Bind(wx.EVT_BUTTON, self._on_add_item, id=wx.ID_ADD)
		wnd.Bind(wx.EVT_BUTTON, self._on_del_item, id=wx.ID_DELETE)
		self._items_lctrl.Bind(wx.EVT_LISTBOX, self._on_list_item_activate)
		wnd.Bind(wx.EVT_BUTTON, self._on_btn_delete, self['btn_deleted'])

	def _on_ok(self, evt):
		BaseDialog._on_ok(self, evt)

	def _on_add_item(self, _evt):
		""" Action for add item button. """
		self._on_save(None)  # wymuszone zapisanie zmian
		self._display_item(self._item_class())  # tworzenie ob; pylint: disable=E1102

	def _on_save(self, _evt):
		""" Save selected & edited item. """
		if not self._displayed_item:
			return
		if not self._wnd.Validate():
			return
		if not self._wnd.TransferDataFromWindow():
			return
		self._displayed_item.update_modify_time()
		self._session.add(self._displayed_item)  # pylint: disable=E1101
		self._session.commit()  # pylint: disable=E1101
		self._refresh_list()
		Publisher().sendMessage('dict.update')

	def _on_del_item(self, _evt):
		""" Acton for delete item button. """
		sel = self._selected_item_uuid
		if sel is None:
			return
		item = self._get_item(sel)
		if not item:
			return
		additional_info = None
		if self._check_children_before_delete(item):
			additional_info = (_('After removal, it cannot be recovered.')
					+ "\n\n"
					+ _("Warning: this affect another items!"))
		if mbox.message_box_delete_confirm(self._wnd, self._item_name + ' "' +
				item.title + '"', additional_info):
			if hasattr(item, 'deleted'):
				item.deleted = datetime.datetime.now()
			else:
				self._session.delete(item)  # pylint: disable=E1101
			self._session.commit()  # pylint: disable=E1101
			self._refresh_list()
			Publisher().sendMessage('dict.delete')
			return True

	def _on_list_item_activate(self, _evt):
		""" Items on list is activated. """
		uuid = self._selected_item_uuid
		item = self._get_item(uuid)
		self._display_item(item)

	def _on_btn_delete(self, _evt):
		items = self._item_class.get_deleted(session=self._session,
				order_by='title')
		if DlgTrash(self._wnd, items, self._session).run(modal=True):
			self._refresh_list()

	def _refresh_list(self,):
		""" Refresh list of all elements. """
		self._displayed_item = None
		self._items_lctrl.Clear()
		for title, uuid in self._get_items():
			self._items_lctrl.Append(title, uuid)
		self._set_buttons_state()

	@property
	def _selected_item_uuid(self):
		""" Get UUID currently selected element on list. """
		sel = self._items_lctrl.GetSelection()
		if sel == wx.NOT_FOUND:
			return None
		return self._items_lctrl.GetClientData(sel)

	def _get_item(self, uuid):
		""" Get item from database on the basis of uuid. """
		return self._item_class.get(self._session, uuid=uuid)

	def _get_items(self):
		""" Get all items given class from database. """
		items = self._item_class.all(session=self._session, order_by='title')
		for obj in items:
			yield obj.title, obj.uuid

	def _display_item(self, item):
		""" Display item in window. """
		self._displayed_item = item
		self._set_buttons_state()
		self._wnd.TransferDataToWindow()

	def _set_buttons_state(self):
		""" Set state of buttons in window. """
		item_in_edit = self._displayed_item is not None
		self[wx.ID_SAVE].Enable(item_in_edit)
		self[wx.ID_DELETE].Enable(item_in_edit)
		self['tc_title'].Enable(item_in_edit)
		self['tc_note'].Enable(item_in_edit)
		self['colorselect'].Enable(item_in_edit)

	def _check_children_before_delete(self, item):
		if hasattr(item, 'children') and bool(item.children):
			return True
		if hasattr(item, 'tasks') and bool(item.tasks):
			return True
		return False
