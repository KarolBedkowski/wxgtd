# -*- coding: utf-8 -*-
""" Select tags dialog.

Copyright (c) Karol Będkowski, 2013

This file is part of wxGTD
Licence: GPLv2+
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2013"
__version__ = "2013-04-28"

import gettext
import logging

import wx

from wxgtd.model.objects import Session, Tag

from ._base_dialog import BaseDialog

_LOG = logging.getLogger(__name__)
_ = gettext.gettext


class DlgSelectTags(BaseDialog):
	""" Select tags dialog.

	Args:
		parent: parent window
		selected: list of uuid selected tags.
	"""

	def __init__(self, parent, selected=None):
		self._tagslist = None
		self._clb_tags = None
		BaseDialog.__init__(self, parent, 'dlg_select_tags', save_pos=False)
		self._setup(selected)
		self._show_tags()

	def _load_controls(self, wnd):
		BaseDialog._load_controls(self, wnd)
		self._clb_tags = self['clb_tags']

	def _create_bindings(self, wnd):
		BaseDialog._create_bindings(self, wnd)
		wnd.Bind(wx.EVT_BUTTON, self._on_add_tag, id=wx.ID_ADD)

	def _setup(self, selected):
		_LOG.debug("DlgSelectTags(%r)", selected)
		self._session = Session()
		self.selected_tags = selected

	def _on_ok(self, evt):
		if not self._wnd.Validate():
			return
		if not self._wnd.TransferDataFromWindow():
			return
		self.selected_tags = self._get_selected_tags()
		BaseDialog._on_ok(self, evt)

	def _on_add_tag(self, _evt):
		new_tag = self['tc_new_tag'].GetValue().strip()
		if not new_tag:
			dlg = wx.MessageDialog(self._wnd, _("Please enter tag name."),
					_("New Tag"))
			dlg.ShowModal()
			dlg.Destroy()
			return
		tag = Tag()
		tag.title = new_tag
		self._session.add(tag)  # pylint: disable=E1101
		self._session.commit()  # pylint: disable=E1101
		self._show_tags()

	def _show_tags(self):
		selected_tags = self.selected_tags
		self._clb_tags.Clear()
		self._tagslist = []
		for tag in self._session.query(Tag):  # pylint: disable=E1101
			num = self._clb_tags.Append(tag.title)
			if wx.Platform == '__WXMSW__':
				self._tagslist.append(tag.uuid)
			else:
				self._clb_tags.SetClientData(num, tag.uuid)
			if tag.uuid in selected_tags:
				self._clb_tags.Check(num, True)

	def _get_selected_tags(self):
		cbl = self._clb_tags
		if wx.Platform == '__WXMSW__':
			checked = [self._tagslist[num] for num in xrange(cbl.GetCount())
					if cbl.IsChecked(num)]
		else:
			checked = [cbl.GetClientData(num) for num in xrange(cbl.GetCount())
					if cbl.IsChecked(num)]
		return checked
