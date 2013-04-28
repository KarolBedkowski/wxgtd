# -*- coding: utf-8 -*-
""" Base class for dialogs.

Copyright (c) Karol Będkowski, 2013

This file is part of wxGTD
Licence: GPLv2+
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2010-2013"
__version__ = "2013-04-27"

import weakref

import wx
from wx import xrc

from wxgtd.lib.appconfig import AppConfig
from wxgtd.wxtools import iconprovider
from wxgtd.wxtools import wxresources


class BaseDialog:
	""" Base class for dialogs defined in xrc files.

	Args:
		parent: parent window
		dialog_name: name dialog in resource file
		resource: name of resource file
		icon: optional icon name
		save_pos: is position of this dialog should be saved & restored.
	"""

	# dict holding opened dialogs
	_windows = weakref.WeakValueDictionary()

	def __init__(self, parent, dialog_name='dialog', resource='wxgtd.xrc',
			icon=None, save_pos=True):
		self._dialog_name = dialog_name
		self._obj_key = None
		self._save_pos = save_pos
		# load resource & create wind
		res = wxresources.load_xrc_resource(resource)
		assert res is not None, 'resource %s not found' % resource
		self._wnd = res.LoadDialog(parent, dialog_name)
		assert self._wnd is not None, 'wnd %s not found in %s' % (dialog_name,
				resource)
		self._wnd.SetExtraStyle(wx.WS_EX_VALIDATE_RECURSIVELY)
		# setup
		self._appconfig = AppConfig()
		self._load_controls(self._wnd)
		self._create_bindings()
		self._setup_wnd(icon)

	@property
	def wnd(self):
		return self._wnd

	@classmethod
	def create(cls, key, *args, **kwargs):
		""" Create or return existing window associate to given key.

		Args:
			key: identifier used to distinguish windows and object
			args, kwargs: argument for constructor given subclass.

		Returns:
			Dialog.
		"""
		if not key:
			return cls(*args, **kwargs)
		dlg = cls._windows.get(key)
		if dlg:
			wx.CallAfter(dlg.wnd.Raise)
		else:
			cls._windows[key] = dlg = cls(*args, **kwargs)
			dlg._obj_key = key
		return dlg

	def run(self, modal=False):
		""" Run (show) dialog.

		Args:
			modal: show dialog as modal window.
		"""
		if modal:
			res = self._wnd.ShowModal() in (wx.ID_OK, wx.ID_SAVE)
			self._wnd.Destroy()
			return res
		self._wnd.Show()

	def __getitem__(self, key):
		""" Get dialog element (widget).

		Args:
			key: name or id widget

		Returns:
			widget.
		"""
		if isinstance(key, (str, unicode)):
			ctrl = xrc.XRCCTRL(self._wnd, key)
		else:
			ctrl = self._wnd.FindWindowById(key)
		assert ctrl is not None, 'ctrl %s not found' % key
		return ctrl

	def _setup_wnd(self, icon):
		""" Setup window.

		Args:
			icon: name of icon; if empty try to use icon from parent window.
		"""
		if not icon:
			parent = self._wnd.GetParent()
			if parent and hasattr(parent, 'GetIcon'):
				self._wnd.SetIcon(parent.GetIcon())
		else:
			self._wnd.SetIcon(iconprovider.get_icon(icon))
		_fix_panels(self._wnd)
		if wx.Platform == '__WXMSW__':
			self._wnd.SetBackgroundColour(wx.SystemSettings.GetColour(
					wx.SYS_COLOUR_ACTIVEBORDER))
		if self._save_pos:
			size = self._appconfig.get(self._dialog_name, 'size', (400, 300))
			if size:
				self._wnd.SetSize(size)
			position = self._appconfig.get(self._dialog_name, 'position')
			if position:
				self._wnd.Move(position)
		else:
			self._wnd.Centre()
		self._wnd.SetFocus()
		self._wnd.SetEscapeId(wx.ID_CLOSE)

	def _load_controls(self, wnd):
		""" Load/create additional controls. """
		pass

	def _create_bindings(self):
		""" Create default bindings."""
		wnd = self._wnd
		wnd.Bind(wx.EVT_CLOSE, self._on_close)
		wnd.Bind(wx.EVT_BUTTON, self._on_cancel, id=wx.ID_CLOSE)
		wnd.Bind(wx.EVT_BUTTON, self._on_save, id=wx.ID_SAVE)
		wnd.Bind(wx.EVT_BUTTON, self._on_ok, id=wx.ID_OK)
		wnd.Bind(wx.EVT_BUTTON, self._on_cancel, id=wx.ID_CANCEL)

	def _on_close(self, _evt):
		""" Action launched on close event. """
		if self._save_pos:
			# save size & posiotion
			self._appconfig.set(self._dialog_name, 'size',
					self._wnd.GetSizeTuple())
			self._appconfig.set(self._dialog_name, 'position',
					self._wnd.GetPositionTuple())
		# remove from cache.
		if self._obj_key and self._obj_key in self._windows:
			del self._windows[self._obj_key]
		self._wnd.Destroy()

	def _on_cancel(self, _evt):
		""" Action for cancel - close window. """
		if self._wnd.IsModal():
			self._wnd.EndModal(wx.ID_CLOSE)
		else:
			self._wnd.Close()

	def _on_ok(self, _evt):
		""" Action for ok/yes - close window. """
		if self._wnd.IsModal():
			self._wnd.EndModal(wx.ID_OK)
		else:
			self._wnd.Close()

	def _on_save(self, evt):
		""" Action for save action. Default - use _on_ok action. """
		self._on_ok(evt)


def _fix_panels(wnd):
	""" Rekursywne ustawienie własności na widgetach """
	for child in wnd.GetChildren():
		if isinstance(child, wx.Panel):
			if wx.Platform == '__WXMSW__':
				child.SetBackgroundColour(wx.SystemSettings.GetColour(
						wx.SYS_COLOUR_ACTIVEBORDER))
			_fix_panels(child)
		elif isinstance(child, wx.Notebook):
			# bez tego walidatory nie działają
			child.SetExtraStyle(wx.WS_EX_VALIDATE_RECURSIVELY)
			_fix_panels(child)
