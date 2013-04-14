# -*- coding: utf-8 -*-

""" Klasa bazowa dla wszystkich dlg, które sterują słownikami.
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2013"
__version__ = "2013-04-14"

import gettext
import logging

import wx

from wxgtd.model.objects import Session

from _base_dialog import BaseDialog
import message_boxes as mbox

_LOG = logging.getLogger(__name__)
_ = gettext.gettext


class DictBaseDlg(BaseDialog):

	_items_list_control = "lb_items"  # nazwa widgeta zawierającego listę
			# elementów
	_item_name = ""  # nazwa elementu
	_item_class = None  # klasa obiektów

	def __init__(self, parent, dlg_name):
		self._displayed_item = None  # aktualnie wuświetlany obiekt

		class _Proxy(object):
			""" Klasa proxy dla obejścia braku dynamiki w walidatorach"""
			def __getattr__(selfi, key):
				if not self._displayed_item:
					return ""
				return getattr(self._displayed_item, key)

			def __setattr__(selfi, key, val):
				setattr(self._displayed_item, key, val)

		self._proxy = _Proxy()
		self._current_selected_uuid = None
		BaseDialog.__init__(self, parent, dlg_name, save_pos=False)
		self._session = Session()
		wx.CallAfter(self._refresh_list)

	def _load_controls(self, wnd):
		BaseDialog._load_controls(self, wnd)
		self._items_lctrl = self[self._items_list_control]

	def _create_bindings(self):
		BaseDialog._create_bindings(self)
		self._wnd.Bind(wx.EVT_BUTTON, self._on_add_item, id=wx.ID_ADD)
		self._wnd.Bind(wx.EVT_BUTTON, self._on_del_item, id=wx.ID_DELETE)
		self._items_lctrl.Bind(wx.EVT_LISTBOX, self._on_list_item_activate)

	def _on_ok(self, evt):
		BaseDialog._on_ok(self, evt)

	def _on_add_item(self, _evt):
		self._on_save(None)  # wymuszone zapisanie zmian
		self._display_item(self._item_class())

	def _on_save(self, _evt):
		if not self._displayed_item:
			return
		if not self._wnd.Validate():
			return
		if not self._wnd.TransferDataFromWindow():
			return
		self._session.add(self._displayed_item)
		self._session.commit()
		self._refresh_list()

	def _on_del_item(self, _evt):
		sel = self._selected_item_uuid
		if sel is None:
			return
		if mbox.message_box_delete_confirm(self._wnd, self._item_name):
			item = self._get_item(sel)
			if item:
				self._session.delete(item)
				self._session.commit()
			self._refresh_list()
			return True

	def _on_list_item_activate(self, _evt):
		uuid = self._selected_item_uuid
		item = self._get_item(uuid)
		self._display_item(item)

	def _refresh_list(self,):
		""" Odświeżenie listy elementów """
		self._displayed_item = None
		self._items_lctrl.Clear()
		for title, uuid in self._get_items():
			self._items_lctrl.Append(title, uuid)
		self._set_buttons_state()

	@property
	def _selected_item_uuid(self):
		""" UUID aktualnie zaznaczonego elementu na liście """
		sel = self._items_lctrl.GetSelection()
		if sel == wx.NOT_FOUND:
			return None
		return self._items_lctrl.GetClientData(sel)

	def _get_item(self, uuid):
		""" Pobranie jednego elementu wg uuid """
		return self._session.query(self._item_class).filter_by(uuid=uuid).first()

	def _get_items(self):
		""" Pobranie wszystkich elementów do wyświetlenia """
		for obj in self._session.query(self._item_class):
			yield obj.title, obj.uuid

	def _display_item(self, item):
		""" Wyświetlenie elementu w oknie """
		self._displayed_item = item
		self._set_buttons_state()
		self._wnd.TransferDataToWindow()

	def _set_buttons_state(self):
		""" Ustawienie stanu przycisków """
		item_in_edit = self._displayed_item is not None
		self[wx.ID_SAVE].Enable(item_in_edit)
		self[wx.ID_DELETE].Enable(item_in_edit)
