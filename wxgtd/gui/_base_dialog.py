# -*- coding: utf-8 -*-

"""
Klasa bazowa dla wszystkich dlg.
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2010-2013"
__version__ = "2010-11-25"

import weakref

import wx
from wx import xrc

from wxgtd.lib import wxresources
from wxgtd.lib.appconfig import AppConfig
from wxgtd.lib import iconprovider


class BaseDialog:
	_windows = weakref.WeakValueDictionary()

	def __init__(self, parent, name='dialog', resource='wxgtd.xrc', icon='wxgtd',
			save_pos=True):
		self._name = name
		self._obj_key = None
		self._save_pos = save_pos
		res = wxresources.load_xrc_resource(resource)
		assert res is not None, 'resource %s not found' % resource
		self._wnd = res.LoadDialog(parent, name)
		assert self._wnd is not None, 'wnd %s not found in %s' % (name, resource)
		self._appconfig = AppConfig()
		self._load_controls(self._wnd)
		self._create_bindings()
		self._setup_wnd(icon, save_pos)

	@classmethod
	def create(cls, key, *args, **kwargs):
		""" Utworzenie okna jeżeli należy zachować pojedyńcze okno dla obiektu
			@param key - identyfikator obiektu dla którego tworzone jest okno
		"""
		if not key:
			return cls(*args, **kwargs)
		dlg = cls._windows.get(key)
		if dlg:
			wx.CallAfter(dlg._wnd.Raise)
		else:
			cls._windows[key] = dlg = cls(*args, **kwargs)
			dlg._obj_key = key
		return dlg

	def run(self, modal=False):
		if modal:
			res = self._wnd.ShowModal() in (wx.ID_OK, wx.ID_SAVE)
			self._wnd.Destroy()
			return res
		self._wnd.Show()

	def __getitem__(self, key):
		if isinstance(key, (str, unicode)):
			ctrl = xrc.XRCCTRL(self._wnd, key)
		else:
			ctrl = self._wnd.FindWindowById(key)
		assert ctrl is not None, 'ctrl %s not found' % key
		return ctrl

	def _setup_wnd(self, icon, save_pos):
		self._wnd.SetIcon(iconprovider.get_icon(icon))
		if wx.Platform == '__WXMSW__':
			self._wnd.SetBackgroundColour(wx.SystemSettings.GetColour(
					wx.SYS_COLOUR_ACTIVEBORDER))
		if save_pos:
			size = self._appconfig.get(self._name, 'size', (400, 300))
			if size:
				self._wnd.SetSize(size)
			position = self._appconfig.get(self._name, 'position')
			if position:
				self._wnd.Move(position)
		self._wnd.SetFocus()
		self._wnd.SetEscapeId(wx.ID_CLOSE)

	def _load_controls(self, wnd):
		pass

	def _create_bindings(self):
		self._wnd.Bind(wx.EVT_CLOSE, self._on_close)
		self._wnd.Bind(wx.EVT_BUTTON, self._on_cancel, id=wx.ID_CLOSE)
		self._wnd.Bind(wx.EVT_BUTTON, self._on_save, id=wx.ID_SAVE)
		self._wnd.Bind(wx.EVT_BUTTON, self._on_ok, id=wx.ID_OK)
		self._wnd.Bind(wx.EVT_BUTTON, self._on_cancel, id=wx.ID_CANCEL)

	def _on_close(self, evt):
		if self._save_pos:
			self._appconfig.set(self._name, 'size', self._wnd.GetSizeTuple())
			self._appconfig.set(self._name, 'position', self._wnd.GetPositionTuple())
		if self._obj_key and self._obj_key in self._windows:
			del self._windows[self._obj_key]
		self._wnd.Destroy()

	def _on_cancel(self, _evt):
		if self._wnd.IsModal():
			self._wnd.EndModal(wx.ID_CLOSE)
		else:
			self._wnd.Close()

	def _on_ok(self, _evt):
		if self._wnd.IsModal():
			self._wnd.EndModal(wx.ID_OK)
		else:
			self._wnd.Close()

	def _on_save(self, evt):
		self._on_ok(evt)
