# -*- coding: utf-8 -*-
""" Main application window.

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
from wx import xrc
import wx.lib.dialogs

from wxgtd.lib.appconfig import AppConfig
from wxgtd.wxtools import wxresources
from wxgtd.wxtools import iconprovider

_ = gettext.gettext
_LOG = logging.getLogger(__name__)


class BaseFrame(object):
	""" Base window class. """

	# pylint: disable=R0903

	_xrc_resource = None
	_window_name = None
	_window_icon = None

	def __init__(self, parent=None):
		self._appconfig = AppConfig()
		self.wnd = self._load_window(parent)
		self._load_controls()
		self._create_toolbar()
		self._create_bindings(self.wnd)
		self._setup_wnd(self.wnd)

	def __getitem__(self, key):
		if isinstance(key, (str, unicode)):
			ctrl = xrc.XRCCTRL(self.wnd, key)
		else:
			ctrl = self.wnd.FindWindowById(key)
		if ctrl is None:
			ctrl = self.wnd.GetMenuBar().FindItemById(xrc.XRCID(key))
		assert ctrl is not None, 'Control %r not found' % key
		return ctrl

	def _setup_wnd(self, wnd):
		if self._window_icon:
			wnd.SetIcon(iconprovider.get_icon(self._window_icon))

		if wx.Platform == '__WXMSW__':
			# fix controls background
			bgcolor = wx.SystemSettings.GetColour(wx.SYS_COLOUR_ACTIVEBORDER)
			wnd.SetBackgroundColour(bgcolor)
			#_update_color(wnd, bgcolor)

		wnd.SetExtraStyle(wx.WS_EX_VALIDATE_RECURSIVELY)
		self._set_size_pos()

	def _load_window(self, parent):
		res = wxresources.load_xrc_resource(self._xrc_resource)
		wnd = res.LoadFrame(parent, self._window_name)
		assert wnd is not None, 'Frame %r not found in %r ' % \
				(self._window_name, self._xrc_resource)
		return wnd

	def _load_controls(self):
		pass

	def _create_bindings(self, wnd):
		wnd.Bind(wx.EVT_CLOSE, self._on_close)

	def _create_menu_bind(self, menu_id, handler):
		self.wnd.Bind(wx.EVT_MENU, handler, id=xrc.XRCID(menu_id))

	def _create_toolbar(self):
		pass

	def _set_size_pos(self):
		appconfig = self._appconfig
		size = appconfig.get(self._window_name, 'size', (800, 600))
		if size:
			self.wnd.SetSize(size)
		position = appconfig.get(self._window_name, 'position')
		if position:
			self.wnd.Move(position)

	# events

	def _on_close(self, _event):
		appconfig = self._appconfig
		appconfig.set(self._window_name, 'size', self.wnd.GetSizeTuple())
		appconfig.set(self._window_name, 'position', self.wnd.GetPositionTuple())
		self.wnd.Destroy()


def _update_color(wnd, bgcolor):
	for child in wnd.GetChildren():
		if isinstance(child, wx.Panel):
			child.SetBackgroundColour(bgcolor)
		_update_color(child, bgcolor)
