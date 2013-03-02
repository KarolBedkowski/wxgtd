# -*- coding: utf-8 -*-
"""
Główne okno programu
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2010"
__version__ = "2011-03-29"

import locale

import wx
from wx import xrc
try:
	from wx.lib.pubsub import pub as Publisher
except ImportError:
	from wx.lib.pubsub import Publisher

from wxgtd.lib import wxresources
from wxgtd.lib.appconfig import AppConfig
from wxgtd.lib import iconprovider
#from wxgtd.lib import wxutils

#from . import dlg_about
#from . import message_boxes as mbox


class FrameMain:
	''' Klasa głównego okna programu'''
	def __init__(self, database):
		self.res = wxresources.load_xrc_resource('wxgtd.xrc')
		self._load_controls()
		self._create_toolbar()
		self._create_bindings()
		self._setup(database)

	def __getitem__(self, key):
		ctrl = xrc.XRCCTRL(self.wnd, key)
		if ctrl is None:
			ctrl = self.wnd.GetMenuBar().FindItemById(xrc.XRCID(key))
		assert ctrl is not None
		return ctrl

	@property
	def _selected_item(self):
		itemid = -1
		while True:
			itemid = self._lc_trips.GetNextItem(itemid, wx.LIST_NEXT_ALL,
					wx.LIST_STATE_SELECTED)
			if itemid == -1:
				break
			yield self._lc_trips.GetItemData(itemid)

	@property
	def _has_selected_items(self):
		return self._lc_trips.GetSelectedItemCount() > 0

	@property
	def selected_tags(self):
		cbl = self._clb_tags
		if wx.Platform == '__WXMSW__':
			checked = [self._tagslist[num] for num in xrange(cbl.GetCount())
					if cbl.IsChecked(num)]
		else:
			checked = [cbl.GetClientData(num) for num in xrange(cbl.GetCount())
					if cbl.IsChecked(num)]
		return checked

	def _setup(self, database):
		self._db = database
		self._chart_ready = False
		self._current_items = []
		self._current_sorting_col = 2
		self._tagslist = []
		self.wnd.SetIcon(iconprovider.get_icon('wxgtd'))

		if wx.Platform == '__WXMSW__':
			bgcolor = wx.SystemSettings.GetColour(wx.SYS_COLOUR_ACTIVEBORDER)
			self.wnd.SetBackgroundColour(bgcolor)

			def update_color(wnd):
				for child in wnd.GetChildren():
					if isinstance(child, wx.Panel):
						child.SetBackgroundColour(bgcolor)
					update_color(child)
			update_color(self.wnd)

		self._set_size_pos()

		appconfig = AppConfig()
		center = appconfig.get('frame_main', 'map_center')
		zoom = appconfig.get('frame_main', 'map_zoom')

	def _load_controls(self):
		self.wnd = self.res.LoadFrame(None, 'frame_main')
		assert self.wnd is not None

	def _create_bindings(self):
		wnd = self.wnd
		wnd.Bind(wx.EVT_CLOSE, self._on_close)

	def _set_size_pos(self):
		appconfig = AppConfig()
		size = appconfig.get('frame_main', 'size')
		if size:
			self.wnd.SetSize(size)
		position = appconfig.get('frame_main', 'position')
		if position:
			self.wnd.Move(position)

	def _create_toolbar(self):
		toolbar = self.wnd.CreateToolBar()
		toolbar.Realize()

	def _on_close(self, _event):
		appconfig = AppConfig()
		appconfig.set('frame_main', 'size', self.wnd.GetSizeTuple())
		appconfig.set('frame_main', 'position', self.wnd.GetPositionTuple())
		self.wnd.Destroy()

	def _on_date_range_change(self, evt):
		self._update_trips_list()
		evt.Skip()

	def _on_sport_change(self, evt):
		self._update_trips_list()
		evt.Skip()


def format_float(value):
	"""docstring for format_float"""
	if value is not None:
		return locale.format('%0.2f', value)
	return ''
