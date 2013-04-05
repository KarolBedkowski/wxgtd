# -*- coding: utf-8 -*-
"""
Główne okno programu
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2010"
__version__ = "2011-03-29"

import sys
import gettext
import logging

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
from wxgtd.model import loader
from wxgtd.gui import dlg_about
from wxgtd.gui._filtertreectrl import FilterTreeCtrl
from wxgtd.gui.dlg_task import DlgTask
from wxgtd.gui import _fmt as fmt
#from . import message_boxes as mbox

_ = gettext.gettext
_LOG = logging.getLogger(__name__)


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
		self._items_path = []
		items_list = self._items_list_ctrl
		items_list.InsertColumn(0, _('Type'), width=50)
		items_list.InsertColumn(1, _('Title'), width=400)
		items_list.InsertColumn(2, _('Context'), width=100)
		items_list.InsertColumn(3, _('Status'), width=100)
		items_list.InsertColumn(4, _('Duo'), width=150)
		self._filter_tree_ctrl.RefreshItems()
		wx.CallAfter(self._refresh_list)

	def _setup_wnd(self):
		self.wnd.SetIcon(iconprovider.get_icon('wxgtd'))
		self._icons = icon_prov = iconprovider.IconProvider()
		icon_prov.load_icons(['project', 'task_done', 'checklist', 'task'])
		self._items_list_ctrl.AssignImageList(icon_prov.image_list,
				wx.IMAGE_LIST_SMALL)

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
		wnd.Bind(wx.EVT_BUTTON, self._on_btn_path_back, id=wx.ID_BACKWARD)

		Publisher.subscribe(self._on_tasks_update, ('task', 'update'))

	def _create_toolbar(self):
		toolbar = self.wnd.CreateToolBar()
		tbi = toolbar.AddLabelTool(-1, _('New Task'), wx.ArtProvider.GetBitmap(
				wx.ART_NEW, wx.ART_TOOLBAR), shortHelp=_('Add new task'))
		self.wnd.Bind(wx.EVT_TOOL, self._on_menu_file_new_task, id=tbi.GetId())

		# show subtask
		self._btn_show_subtasks = wx.ToggleButton(toolbar, -1,
				_(" Show subtasks "))
		toolbar.AddControl(self._btn_show_subtasks)
		self.wnd.Bind(wx.EVT_TOGGLEBUTTON, self._on_btn_show_subtasks,
				self._btn_show_subtasks)

		# show completed
		self._btn_show_finished = wx.ToggleButton(toolbar, -1,
				_(" Show finished "))
		toolbar.AddControl(self._btn_show_finished)
		self.wnd.Bind(wx.EVT_TOGGLEBUTTON, self._on_btn_show_finished,
				self._btn_show_finished)

		# hide until due
		self._btn_hide_due = wx.ToggleButton(toolbar, -1,
				_(" Hide due "))
		toolbar.AddControl(self._btn_hide_due)
		self.wnd.Bind(wx.EVT_TOGGLEBUTTON, self._on_btn_hide_due,
				self._btn_hide_due)

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
		dlg = wx.FileDialog(self.wnd, style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
		if dlg.ShowModal() == wx.ID_OK:
			filename = dlg.GetPath()
			loader.load_from_file(filename)
			self._filter_tree_ctrl.RefreshItems()
			Publisher.sendMessage('task.update')
		dlg.Destroy()

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
		self._items_path = []
		wx.CallAfter(self._refresh_list)
		evt.Skip()

	def _on_items_list_activated(self, evt):
		task_uuid, task_type = self._items_uuids[evt.GetData()]
		if task_type in (OBJ.TYPE_PROJECT, OBJ.TYPE_CHECKLIST):
			session = OBJ.Session()
			task = session.query(OBJ.Task).filter_by(uuid=task_uuid).first()
			session.close()
			self._items_path.append(task)
			self._refresh_list()
			return
		if task_uuid:
			dlg = DlgTask.create(task_uuid, self.wnd, task_uuid)
			dlg.run()

	def _on_btn_path_back(self, _evt):
		if self._items_path:
			self._items_path.pop(-1)
			self._refresh_list()

	def _on_tasks_update(self, _args):
		self._refresh_list()

	def _on_btn_hide_due(self, _evt):
		self._refresh_list()

	def _on_btn_show_subtasks(self, _evt):
		self._refresh_list()

	def _on_btn_show_finished(self, _evt):
		self._refresh_list()

	# logic

	def _refresh_list(self):
		group_id = self['rb_show_selection'].GetSelection()
		tmodel = self._filter_tree_ctrl.model
		params = {'starred': False, 'finished': None, 'min_priority': None,
				'max_start_date': None, 'max_due_date': None, 'tags': None,
				'types': None}
		params['contexts'] = list(tmodel.checked_items_by_parent("CONTEXTS"))
		params['folders'] = list(tmodel.checked_items_by_parent("FOLDERS"))
		params['goals'] = list(tmodel.checked_items_by_parent("GOALS"))
		params['statuses'] = list(tmodel.checked_items_by_parent("STATUSES"))
		params['parent_uuid'] = parent = self._items_path[-1].uuid \
				if self._items_path else None
		params['tags'] = list(tmodel.checked_items_by_parent("TAGS"))
		params['finished'] = self._btn_show_finished.GetValue()
		if not parent:
			if not self._btn_show_subtasks.GetValue():
				# tylko nadrzędne
				params['parent_uuid'] = 0
		if group_id == 0:  # all
			pass
		elif group_id == 1:  # hot
			# TODO: dodać obsługę hotlisty
			# będzie to problematyczne, bo hotlista może działać na and-ach lub
			# na orach (domyślne). And można tutaj dodać, ale dla or-ów musi
			# być osobna metoda do zwracania
			pass
		elif group_id == 2:  # stared
			params['starred'] = True
		elif group_id == 3:  # basket
			# no status, no context
			params['contexts'] = [None]
			params['statuses'] = [None]
		elif group_id == 4:  # finished
			params['finished'] = True
		elif group_id == 5:  # projects
			if not parent:
				params['types'] = [OBJ.TYPE_PROJECT]
		elif group_id == 6:  # checklists
			if parent:
				params['types'] = [OBJ.TYPE_CHECKLIST, OBJ.TYPE_CHECKLIST_ITEM]
			else:
				params['types'] = [OBJ.TYPE_CHECKLIST]

		_LOG.debug("FrameMain._refresh_list; params=%r", params)
		tasks = OBJ.Task.select_by_filters(**params)
		items_list = self._items_list_ctrl
		items_list.Freeze()
		items_list.DeleteAllItems()
		self._items_uuids.clear()
		icon_task = self._icons.get_image_index('task')
		icon_project = self._icons.get_image_index('project')
		icon_checklist = self._icons.get_image_index('checklist')
		icon_task_done = self._icons.get_image_index('task_done')
		for task in tasks:
			if task.type == OBJ.TYPE_PROJECT:
				icon = icon_project
			elif task.type == OBJ.TYPE_CHECKLIST:
				icon = icon_checklist
			elif task.completed:
				icon = icon_task_done
			else:
				icon = icon_task
			idx = items_list.InsertImageStringItem(sys.maxint,
					OBJ.TYPES[task.type], icon)
			items_list.SetStringItem(idx, 1, task.title)
			items_list.SetStringItem(idx, 2, task.context.title if task.context
					else '')
			items_list.SetStringItem(idx, 3, task.status_name)
			items_list.SetStringItem(idx, 4, fmt.format_timestamp(task.due_date,
					task.due_time_set))
			items_list.SetItemData(idx, idx)
			self._items_uuids[idx] = (task.uuid, task.type)
		items_list.Thaw()
		self.wnd.SetStatusText(_("Showed %d items") % items_list.GetItemCount())

		path_str = ' / '.join(task.title for task in self._items_path)
		self['l_path'].SetLabel(path_str)
		self.wnd.FindWindowById(wx.ID_BACKWARD).Enable(bool(self._items_path))


def _update_color(wnd, bgcolor):
	for child in wnd.GetChildren():
		if isinstance(child, wx.Panel):
			child.SetBackgroundColour(bgcolor)
		_update_color(child, bgcolor)
