# -*- coding: utf-8 -*-
""" Search tasks frame.

Copyright (c) Karol Będkowski, 2013

This file is part of wxGTD
Licence: GPLv2+
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2013"
__version__ = "2013-05-23"

import gettext
import logging

import wx

from wxgtd.model import objects as OBJ
from wxgtd.gui._base_frame import BaseFrame
from wxgtd.gui import _tasklistctrl as TLC

_ = gettext.gettext
ngettext = gettext.ngettext  # pylint: disable=C0103
_LOG = logging.getLogger(__name__)


class FrameSeach(BaseFrame):
	""" Search tasks window class. """
	# pylint: disable=R0903, R0902

	_xrc_resource = 'wxgtd.xrc'
	_window_name = 'frame_search'
	_window_icon = 'wxgtd'
	_instance = None

	def __init__(self):
		BaseFrame.__init__(self)
		self._setup()

	@classmethod
	def run(cls):
		if cls._instance is not None:
			cls._instance.wnd.Raise()
		else:
			cls._instance = cls()
			cls._instance.wnd.Show()

	def _setup(self):
		self._searchbox.SetDescriptiveText(_('Search'))
		self._searchbox.ShowCancelButton(True)
		self._searchbox.ShowSearchButton(True)
		self._session = OBJ.Session()

	def _load_controls(self):
		# pylint: disable=W0201
		BaseFrame._load_controls(self)
		tasklist_panel = self['panel_tasks']
		self._items_list_ctrl = TLC.TaskListControl(tasklist_panel)
		box = wx.BoxSizer()
		box.Add(self._items_list_ctrl, 1, wx.EXPAND)
		self['panel_tasks'].SetSizer(box)
		self._searchbox = self['sc_search']

	def _create_bindings(self, wnd):
		BaseFrame._create_bindings(self, wnd)
		#self.wnd.Bind(wx.EVT_TEXT, self._on_search, self._searchbox)
		self.wnd.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN, self._on_search,
				self._searchbox)
		self.wnd.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self._on_search_cancel,
				self._searchbox)
		self.wnd.Bind(wx.EVT_TEXT_ENTER, self._on_search, self._searchbox)
		self.wnd.Bind(wx.EVT_BUTTON, self._on_search, id=wx.ID_FIND)

	# events

	def _on_close(self, event):
		FrameSeach._instance = None
		self._session.close()
		BaseFrame._on_close(self, event)

	def _on_search(self, _evt):
		self._refresh_list()

	def _on_search_cancel(self, _evt):
		if self._searchbox.GetValue():
			self._searchbox.SetValue('')
		self._refresh_list()

	def _refresh_list(self):
		wx.SetCursor(wx.HOURGLASS_CURSOR)
		self.wnd.Freeze()
		text = self._searchbox.GetValue()
		tasks = []
		active_only = not self['cb_search_finished'].GetValue()
		if text:
			tasks = OBJ.Task.search(text, active_only, self._session)
		self._items_list_ctrl.fill(tasks, active_only=active_only)
		showed = self._items_list_ctrl.GetItemCount()
		self.wnd.SetStatusText(ngettext("%d item", "%d items", showed) % showed, 1)
		self.wnd.Thaw()
		wx.SetCursor(wx.STANDARD_CURSOR)
