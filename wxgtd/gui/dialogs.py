#!/usr/bin/python
# -*- coding: utf-8 -*-
""" Common dialogs.

Copyright (c) Karol Będkowski, 2013

This file is part of wxGTD

This is free software; you can redistribute it and/or modify it under the
terms of the GNU General Public License as published by the Free Software
Foundation, version 2.
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2004-2013"
__version__ = "2013-05-19"


import gettext

import wx

_ = gettext.gettext


class MultilineTextDialog(wx.Dialog):
	""" Custom message box dialog.

	Args:
		parent: parent window
		text: text to display
		windows_title: optional dialog title
		label: optional label to show above text ctrl
		buttons: buttons ids to create
	"""

	def __init__(self, parent, text=None, windows_title=None, label=None,
			buttons=wx.ID_OK | wx.ID_CLOSE, allow_save_empty=False):
		wx.Dialog.__init__(self, parent, -1, windows_title or '',
				style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
		main_sizer = wx.BoxSizer(wx.VERTICAL)
		sizer_text = wx.BoxSizer(wx.VERTICAL)
		self._allow_save_empty = allow_save_empty

		if label:
			fstyle = wx.SystemSettings_GetFont(wx.SYS_DEFAULT_GUI_FONT)
			fstyle.SetWeight(wx.FONTWEIGHT_BOLD)
			fstyle.SetPointSize(fstyle.GetPointSize() + 2)
			ptext = wx.StaticText(self, -1, label)
			ptext.SetFont(fstyle)
			sizer_text.Add(ptext, 0, wx.EXPAND)
			sizer_text.Add((12, 12))

		self._text_ctrl = wx.TextCtrl(self, -1, text or '',
				style=wx.TE_MULTILINE)
		sizer_text.Add(self._text_ctrl, 1, wx.EXPAND | wx.LEFT,
				12 if label else 0)

		main_sizer.Add(sizer_text, 1, wx.EXPAND | wx.ALL, 12)

		buttons_grid = wx.BoxSizer(wx.HORIZONTAL)
		buttons_grid.Add((12, 12), 1, wx.EXPAND)
		if buttons & wx.ID_CLOSE == wx.ID_CLOSE:
			buttons_grid.Add(wx.Button(self, wx.ID_CLOSE), 0, wx.LEFT, 12)
		if buttons & wx.ID_CANCEL == wx.ID_CANCEL:
			buttons_grid.Add(wx.Button(self, wx.ID_CANCEL), 0, wx.LEFT, 12)
		if buttons & wx.ID_NO == wx.ID_NO:
			buttons_grid.Add(wx.Button(self, wx.ID_NO), 0, wx.LEFT, 12)
		if buttons & wx.ID_OK == wx.ID_OK:
			buttons_grid.Add(wx.Button(self, wx.ID_OK), 0, wx.LEFT, 12)
		if buttons & wx.ID_SAVE == wx.ID_SAVE:
			buttons_grid.Add(wx.Button(self, wx.ID_SAVE), 0, wx.LEFT, 12)
		if buttons & wx.ID_YES == wx.ID_YES:
			buttons_grid.Add(wx.Button(self, wx.ID_YES), 0, wx.LEFT, 12)
		main_sizer.Add(buttons_grid, 0, wx.EXPAND | wx.ALL, 12)
		self.SetSizerAndFit(main_sizer)

		self.Bind(wx.EVT_BUTTON, self._on_btn)
		self.SetSize((600, 400))

	@property
	def text(self):
		return self._text_ctrl.GetValue().strip()

	def _on_btn(self, evt):
		oid = evt.GetEventObject().GetId()
		if not self._allow_save_empty and oid in (wx.ID_OK, wx.ID_SAVE,
				wx.ID_YES) and not self.text:
			mdlg = wx.MessageDialog(self, _("Empty text is not allowed."),
					_("Error"), wx.OK | wx.ICON_ERROR)
			mdlg.ShowModal()
			mdlg.Destroy()
			return
		self.EndModal(oid)
