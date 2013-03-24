# -*- coding: utf-8 -*-
"""
Główne okno programu
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2010"
__version__ = "2011-03-29"

import sys
import gettext
import time

import wx
from wx import xrc
import wx.lib.customtreectrl as CT
try:
	from wx.lib.pubsub.pub import Publisher
except ImportError:
	from wx.lib.pubsub import Publisher

from wxgtd.lib import wxresources
from wxgtd.lib.appconfig import AppConfig
from wxgtd.lib import iconprovider
#from wxgtd.lib import wxutils

from wxgtd.model import objects as OBJ
from wxgtd.gui import dlg_about
from wxgtd.gui._filtertreectrl import FilterTreeCtrl
from wxgtd.gui.dlg_task import DlgTask
#from . import message_boxes as mbox

_ = gettext.gettext


class FrameMain:
	''' Klasa głównego okna programu'''
	def __init__(self):
		self.res = wxresources.load_xrc_resource('wxgtd.xrc')
		self._load_controls()
		self._create_toolbar()
		self._create_bindings()
		self._setup_wnd()
		self._setup()

	def __getitem__(self, key):
		ctrl = xrc.XRCCTRL(self.wnd, key)
		if ctrl is None:
			ctrl = self.wnd.GetMenuBar().FindItemById(xrc.XRCID(key))
		assert ctrl is not None, 'Control %r not found' % key
		return ctrl

	def _setup(self):
		self._items_uuids = {}
		items_list = self._items_list_ctrl
		items_list.InsertColumn(0, _('Title'), width=400)
		items_list.InsertColumn(1, _('Context'), width=100)
		items_list.InsertColumn(2, _('Status'), width=100)
		items_list.InsertColumn(3, _('Duo'), width=150)
		self._filter_tree_ctrl.RefreshItems()
		wx.CallAfter(self._refresh_list)

	def _setup_wnd(self):
		self.wnd.SetIcon(iconprovider.get_icon('wxgtd'))

		if wx.Platform == '__WXMSW__':
			# fix controls background
			bgcolor = wx.SystemSettings.GetColour(wx.SYS_COLOUR_ACTIVEBORDER)
			self.wnd.SetBackgroundColour(bgcolor)
			_update_color(self.wnd, bgcolor)

		self._set_size_pos()

	def _load_controls(self):
		self.wnd = self.res.LoadFrame(None, 'frame_main')
		assert self.wnd is not None, 'Frame not found'
		self._items_list_ctrl = self['lc_main_list']
		# filter tree ctrl
		filter_tree_panel = self['filter_tree_panel']
		box = wx.BoxSizer(wx.HORIZONTAL)
		self._filter_tree_ctrl = FilterTreeCtrl(filter_tree_panel, -1)
		box.Add(self._filter_tree_ctrl, 1, wx.EXPAND)
		filter_tree_panel.SetSizer(box)

	def _create_bindings(self):
		wnd = self.wnd
		wnd.Bind(wx.EVT_CLOSE, self._on_close)

		def _create_menu_bind(menu_id, handler):
			self.wnd.Bind(wx.EVT_MENU, handler, id=xrc.XRCID(menu_id))

		_create_menu_bind('menu_file_load', self._on_menu_file_load)
		_create_menu_bind('menu_file_exit', self._on_menu_file_exit)
		_create_menu_bind('menu_about', self._on_menu_help_about)

		self._filter_tree_ctrl.Bind(wx.EVT_TREE_ITEM_ACTIVATED,
				self._on_filter_tree_item_activated)
		self._filter_tree_ctrl.Bind(CT.EVT_TREE_ITEM_CHECKED,
				self._on_filter_tree_item_selected)
		self['rb_show_selection'].Bind(wx.EVT_RADIOBOX,
				self._on_rb_show_selection)
		self._items_list_ctrl.Bind(wx.EVT_LIST_ITEM_ACTIVATED,
				self._on_items_list_activated)

		Publisher.subscribe(self._on_tasks_update, ('task', 'update'))

	def _create_toolbar(self):
		toolbar = self.wnd.CreateToolBar()
		tbi = toolbar.AddLabelTool(-1, _('New Task'), wx.ArtProvider.GetBitmap(
				wx.ART_NEW, wx.ART_TOOLBAR), shortHelp=_('Add new task'))
		self.wnd.Bind(wx.EVT_TOOL, self._on_menu_file_new_task, id=tbi.GetId())

		toolbar.Realize()

	def _set_size_pos(self):
		appconfig = AppConfig()
		size = appconfig.get('frame_main', 'size', (800, 600))
		if size:
			self.wnd.SetSize(size)
		position = appconfig.get('frame_main', 'position')
		if position:
			self.wnd.Move(position)

	# events

	def _on_close(self, _event):
		appconfig = AppConfig()
		appconfig.set('frame_main', 'size', self.wnd.GetSizeTuple())
		appconfig.set('frame_main', 'position', self.wnd.GetPositionTuple())
		self.wnd.Destroy()

	def _on_menu_file_load(self, _evt):
		pass

	def _on_menu_file_exit(self, _evt):
		self.wnd.Close()

	def _on_menu_file_new_task(self, _evt):
		task = OBJ.Task()
		dlg = DlgTask.create(task.uuid, self.wnd, task)
		dlg.run()

	def _on_menu_help_about(self, _evt):
		""" Show about dialog """
		dlg_about.show_about_box(self.wnd)

	def _on_filter_tree_item_activated(self, evt):
		wx.CallAfter(self._refresh_list)
		evt.Skip()

	def _on_filter_tree_item_selected(self, evt):
		wx.CallAfter(self._refresh_list)
		evt.Skip()

	def _on_rb_show_selection(self, evt):
		wx.CallAfter(self._refresh_list)
		evt.Skip()

	def _on_items_list_activated(self, evt):
		uuid = self._items_uuids[evt.GetData()]
		task = OBJ.Task.get(uuid=uuid)
		if task:
			dlg = DlgTask.create(task.uuid, self.wnd, task)
			dlg.run()

	def _on_tasks_update(self, _args):
		self._refresh_list()

	# logic

	def _refresh_list(self):
		group_id = self['rb_show_selection'].GetSelection()
		if group_id == 0:  # all
			pass
		elif group_id == 1:  # Hot
			pass
		elif group_id == 2:  # Stared
			pass
		elif group_id == 3:  # basket
			pass
		elif group_id == 4:  # finished
			pass
		tmodel = self._filter_tree_ctrl.model
		contexts = list(tmodel.checked_items_by_parent("CONTEXTS"))
		folders = list(tmodel.checked_items_by_parent("FOLDERS"))
		goals = list(tmodel.checked_items_by_parent("GOALS"))
		statuses = list(tmodel.checked_items_by_parent("STATUSES"))
		tasks = OBJ.Task.select_by_filters(contexts, folders, goals, statuses)
		items_list = self._items_list_ctrl
		items_list.Freeze()
		items_list.DeleteAllItems()
		idx = 0
		self._items_uuids.clear()
		for task in tasks:
			idx = items_list.InsertStringItem(sys.maxint, task.title)
			items_list.SetStringItem(idx, 1, task.context.title if task.context
					else '')
			items_list.SetStringItem(idx, 2, task.status_name)
			items_list.SetStringItem(idx, 3, format_date(task.due_date))
			items_list.SetItemData(idx, idx)
			self._items_uuids[idx] = task.uuid
		items_list.Thaw()
		self.wnd.SetStatusText(_("Showed %d items") % idx)


def _update_color(wnd, bgcolor):
	for child in wnd.GetChildren():
		if isinstance(child, wx.Panel):
			child.SetBackgroundColour(bgcolor)
		_update_color(child, bgcolor)


def format_date(timestamp):
	if not timestamp:
		return ''
	return time.strftime('%x %X', time.localtime(timestamp))
