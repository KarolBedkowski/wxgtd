# -*- coding: utf-8 -*-
# pylint: disable-msg=R0901, R0904, C0103
""" Task bar icon.

Copyright (c) Karol Będkowski, 2013

This file is part of wxGTD
Licence: GPLv2+
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2013"
__version__ = "2013-05-11"

import gettext
import logging

import wx

from wxgtd.wxtools import iconprovider
from wxgtd.gui.frame_notebooks import FrameNotebook
from wxgtd.gui import quicktask

_ = gettext.gettext
_LOG = logging.getLogger(__name__)


class TaskBarIcon(wx.TaskBarIcon):
	TBMENU_RESTORE = wx.NewId()
	TBMENU_CLOSE = wx.NewId()
	TBMENU_SHOW_NOTEBOOK = wx.NewId()
	TBMENU_QUICK_TASK = wx.NewId()

	def __init__(self, parent_frame):
		wx.TaskBarIcon.__init__(self)
		self._frame = parent_frame
		# icon
		img = wx.ImageFromBitmap(iconprovider.get_image('wxgtd'))
		if "wxMSW" in wx.PlatformInfo:
			img = img.Scale(16, 16)
		elif "wxGTK" in wx.PlatformInfo:
			img = img.Scale(22, 22)
		icon = wx.IconFromBitmap(img.ConvertToBitmap())
		self.SetIcon(icon, _("wxGTD"))

		self._create_bindings()

	def CreatePopupMenu(self):
		menu = wx.Menu()
		menu.Append(self.TBMENU_RESTORE, _("Restore wxGTD"))
		menu.Append(self.TBMENU_SHOW_NOTEBOOK, _("Show notebook"))
		menu.AppendSeparator()
		menu.Append(self.TBMENU_QUICK_TASK, _("Quick task..."))
		menu.AppendSeparator()
		menu.Append(self.TBMENU_CLOSE,  _("Close wxGTD"))
		return menu

	def _create_bindings(self):
		self.Bind(wx.EVT_TASKBAR_LEFT_UP, self._on_icon_activate)
		self.Bind(wx.EVT_TASKBAR_LEFT_DCLICK, self._on_icon_activate)
		self.Bind(wx.EVT_MENU, self._on_icon_activate, id=self.TBMENU_RESTORE)
		self.Bind(wx.EVT_MENU, self._on_menu_app_close, id=self.TBMENU_CLOSE)
		self.Bind(wx.EVT_MENU, self._on_menu_show_notebook,
				id=self.TBMENU_SHOW_NOTEBOOK)
		self.Bind(wx.EVT_MENU, self._on_menu_quick_task, id=self.TBMENU_QUICK_TASK)

	def _on_icon_activate(self, _evt):
		if self._frame.IsIconized():
			self._frame.Iconize(False)
		if not self._frame.IsShown():
			self._frame.Show(True)
		self._frame.Raise()

	def _on_menu_app_close(self, _evt):
		wx.CallAfter(self._frame.Close)

	def _on_menu_show_notebook(self, _evt):  # pylint: disable=R0201
		FrameNotebook.run()

	def _on_menu_quick_task(self, _evt):  # pylint: disable=R0201
		quicktask.quick_task()
