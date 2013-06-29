# -*- coding: utf-8 -*-
""" Trash dialog.

Copyright (c) Karol Będkowski, 2013

This file is part of wxGTD
Licence: GPLv2+
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2013"
__version__ = "2013-06-29"

import logging
import gettext

import wx

from wxgtd.gui import message_boxes as msg
from wxgtd.lib import fmt
from wxgtd.logic import dicts as dict_logic
from ._base_dialog import BaseDialog

_ = gettext.gettext
_LOG = logging.getLogger(__name__)


class DlgTrash(BaseDialog):
	""" Trash dialog.

	Args:
		parent: parent window
		items: list of deleted items
		session: SqlAlchemy sesion
	"""

	def __init__(self, parent, items, session):
		BaseDialog.__init__(self, parent, 'dlg_trash')
		self._setup(items, session)

	def _load_controls(self, wnd):
		self._lc_items = self['lc_items']
		self._lc_items.InsertColumn(0, _("Title"))
		self._lc_items.InsertColumn(1, _("Created"))
		self._lc_items.InsertColumn(2, _("Deleted"))

	def _create_bindings(self, wnd):
		BaseDialog._create_bindings(self, wnd)
		wnd.Bind(wx.EVT_BUTTON, self._on_ok, self['btn_undelete'])

	def _setup(self, items, session):
		self._items = list(items)
		self._session = session
		lc_items = self._lc_items
		for idx, item in enumerate(items):
			lc_items.InsertStringItem(idx, item.title)
			lc_items.SetStringItem(idx, 1, fmt.format_timestamp(item.created))
			lc_items.SetStringItem(idx, 2, fmt.format_timestamp(item.deleted))
			lc_items.SetItemData(idx, idx)
		lc_items.SetColumnWidth(0, wx.LIST_AUTOSIZE)
		lc_items.SetColumnWidth(1, wx.LIST_AUTOSIZE)
		lc_items.SetColumnWidth(2, wx.LIST_AUTOSIZE)

	def _on_ok(self, evt):
		if self._lc_items.GetSelectedItemCount() == 0:
			msg.message_box_info(self._wnd,
					_("Please select one or more items to undelete."))
			return
		idx = -1
		while True:
			idx = self._lc_items.GetNextItem(idx, wx.LIST_NEXT_ALL,
				wx.LIST_STATE_SELECTED)
			if idx == -1:
				self._wnd.EndModal(wx.ID_OK)
				return
			item = self._items[self._lc_items.GetItemData(idx)]
			dict_logic.undelete_dict_item(item, self._session)
