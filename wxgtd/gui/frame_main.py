# -*- coding: utf-8 -*-
"""
Główne okno programu
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2010"
__version__ = "2011-03-29"

import os
import gettext
import logging
import datetime

import wx
from wx import xrc
import wx.lib.customtreectrl as CT
try:
	from wx.lib.pubsub.pub import Publisher
except ImportError:
	from wx.lib.pubsub import Publisher

from wxgtd.wxtools import wxresources
from wxgtd.lib.appconfig import AppConfig
from wxgtd.lib import iconprovider
#from wxgtd.lib import wxutils

from wxgtd.model import objects as OBJ
from wxgtd.model import loader
from wxgtd.model import exporter
from wxgtd.model import sync
from wxgtd.model import enums
from wxgtd.model import logic
from wxgtd.gui import dlg_about
from wxgtd.gui import _fmt as fmt
from wxgtd.gui._filtertreectrl import FilterTreeCtrl
from wxgtd.gui.dlg_task import DlgTask
from wxgtd.gui.dlg_checklistitem import DlgChecklistitem
from wxgtd.gui.dlg_preferences import DlgPreferences
from wxgtd.gui.dlg_sync_progress import DlgSyncProggress
from wxgtd.gui.dlg_tags import DlgTags
from wxgtd.gui.dlg_goals import DlgGoals
from wxgtd.gui.dlg_folders import DlgFolders
from wxgtd.gui._tasklistctrl import TaskListControl
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
		self._session = OBJ.Session()
		self._items_path = []
		self._filter_tree_ctrl.RefreshItems()
		wx.CallAfter(self._refresh_list)
		appconfig = AppConfig()
		if appconfig.get('sync', 'sync_on_startup'):
			wx.CallAfter(self._autosync)

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
		# filter tree ctrl
		filter_tree_panel = self['filter_tree_panel']
		box = wx.BoxSizer(wx.HORIZONTAL)
		self._filter_tree_ctrl = FilterTreeCtrl(filter_tree_panel, -1)
		box.Add(self._filter_tree_ctrl, 1, wx.EXPAND)
		filter_tree_panel.SetSizer(box)
		# tasklist
		tasklist_panel = self['tasklist_panel']
		box = wx.BoxSizer(wx.HORIZONTAL)
		self._items_list_ctrl = TaskListControl(tasklist_panel)
		box.Add(self._items_list_ctrl, 1, wx.EXPAND)
		tasklist_panel.SetSizer(box)

	def _create_bindings(self):
		wnd = self.wnd
		wnd.Bind(wx.EVT_CLOSE, self._on_close)

		def _create_menu_bind(menu_id, handler):
			self.wnd.Bind(wx.EVT_MENU, handler, id=xrc.XRCID(menu_id))

		_create_menu_bind('menu_file_load', self._on_menu_file_load)
		_create_menu_bind('menu_file_save', self._on_menu_file_save)
		_create_menu_bind('menu_file_exit', self._on_menu_file_exit)
		_create_menu_bind('menu_file_sync', self._on_menu_file_sync)
		_create_menu_bind('menu_file_preferences',
				self._on_menu_file_preferences)
		_create_menu_bind('menu_help_about', self._on_menu_help_about)
		_create_menu_bind('menu_task_new', self._on_menu_task_new)
		_create_menu_bind('menu_task_edit', self._on_menu_task_edit)
		_create_menu_bind('menu_task_delete', self._on_menu_task_delete)
		_create_menu_bind('menu_sett_tags', self._on_menu_sett_tags)
		_create_menu_bind('menu_sett_goals', self._on_menu_sett_goals)
		_create_menu_bind('menu_sett_folders', self._on_menu_sett_folders)

		self._filter_tree_ctrl.Bind(wx.EVT_TREE_ITEM_ACTIVATED,
				self._on_filter_tree_item_activated)
		self._filter_tree_ctrl.Bind(CT.EVT_TREE_ITEM_CHECKED,
				self._on_filter_tree_item_selected)
		self['rb_show_selection'].Bind(wx.EVT_RADIOBOX,
				self._on_rb_show_selection)
		self._items_list_ctrl.Bind(wx.EVT_LIST_ITEM_ACTIVATED,
				self._on_items_list_activated)
		wnd.Bind(wx.EVT_BUTTON, self._on_btn_path_back, id=wx.ID_UP)
		self['btn_parent_edit'].Bind(wx.EVT_BUTTON, self._on_btn_edit_parent)

		Publisher.subscribe(self._on_tasks_update, ('task', 'update'))
		Publisher.subscribe(self._on_tasks_update, ('task', 'delete'))

	def _create_toolbar(self):
		toolbar = self.wnd.CreateToolBar()
		tbi = toolbar.AddLabelTool(-1, _('New Task'), wx.ArtProvider.GetBitmap(
				wx.ART_NEW, wx.ART_TOOLBAR), shortHelp=_('Add new task'))
		self.wnd.Bind(wx.EVT_TOOL, self._on_btn_new_task, id=tbi.GetId())

		tbi = toolbar.AddLabelTool(-1, _('Edit Task'),
				iconprovider.get_image('task_edit'),
				shortHelp=_('Edit selected task'))
		self.wnd.Bind(wx.EVT_TOOL, self._on_btn_edit_selected_task,
				id=tbi.GetId())

		tbi = toolbar.AddLabelTool(-1, _('Delete Task'),
				iconprovider.get_image('task_delete'),
				shortHelp=_('Delete selected task'))
		self.wnd.Bind(wx.EVT_TOOL, self._on_btn_delete_selected_task,
				id=tbi.GetId())

		toolbar.AddSeparator()

		tbi = toolbar.AddLabelTool(-1, _('Toggle Task Completed'),
				iconprovider.get_image('task_done'),
				shortHelp=_('Toggle selected task completed'))
		self.wnd.Bind(wx.EVT_TOOL, self._on_btn_complete_task, id=tbi.GetId())

		toolbar.AddSeparator()

		appconfig = AppConfig()

		# show subtask
		self._btn_show_subtasks = wx.ToggleButton(toolbar, -1,
				_(" Show subtasks "))
		toolbar.AddControl(self._btn_show_subtasks)
		self.wnd.Bind(wx.EVT_TOGGLEBUTTON, self._on_btn_show_subtasks,
				self._btn_show_subtasks)
		self._btn_show_subtasks.SetValue(appconfig.get('main', 'show_subtask', True))

		# show completed
		self._btn_show_finished = wx.ToggleButton(toolbar, -1,
				_(" Show finished "))
		toolbar.AddControl(self._btn_show_finished)
		self.wnd.Bind(wx.EVT_TOGGLEBUTTON, self._on_btn_show_finished,
				self._btn_show_finished)
		self._btn_show_finished.SetValue(appconfig.get('main', 'show_finished',
				False))

		# hide until due
		self._btn_hide_until = wx.ToggleButton(toolbar, -1,
				_(" Hide until "))
		toolbar.AddControl(self._btn_hide_until)
		self.wnd.Bind(wx.EVT_TOGGLEBUTTON, self._on_btn_hide_due,
				self._btn_hide_until)
		self._btn_hide_until.SetValue(appconfig.get('main', 'show_hide_until', True))

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
		if appconfig.get('sync', 'sync_on_exit'):
			wx.CallAfter(self._autosync)
		appconfig.set('frame_main', 'size', self.wnd.GetSizeTuple())
		appconfig.set('frame_main', 'position', self.wnd.GetPositionTuple())
		appconfig.set('main', 'show_finished', self._btn_show_finished.GetValue())
		appconfig.set('main', 'show_subtask', self._btn_show_subtasks.GetValue())
		appconfig.set('main', 'show_hide_until', self._btn_hide_until.GetValue())
		self.wnd.Destroy()

	def _on_menu_file_load(self, _evt):
		appconfig = AppConfig()
		dlg = wx.FileDialog(self.wnd,
				defaultDir=appconfig.get('files', 'last_dir', ''),
				defaultFile=appconfig.get('files', 'last_file', 'GTD_SYNC.zip'),
				style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
		if dlg.ShowModal() == wx.ID_OK:
			filename = dlg.GetPath()
			loader.load_from_file(filename)
			self._filter_tree_ctrl.RefreshItems()
			Publisher.sendMessage('task.update')
			appconfig.set('files', 'last_dir', os.path.dirname(filename))
			appconfig.set('files', 'last_file', os.path.basename(filename))
		dlg.Destroy()

	def _on_menu_file_save(self, _evt):
		appconfig = AppConfig()
		dlg = wx.FileDialog(self.wnd,
				defaultDir=appconfig.get('files', 'last_dir', ''),
				defaultFile=appconfig.get('files', 'last_file', 'GTD_SYNC.zip'),
				style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
		if dlg.ShowModal() == wx.ID_OK:
			filename = dlg.GetPath()
			exporter.save_to_file(filename)
			self._filter_tree_ctrl.RefreshItems()
			Publisher.sendMessage('task.update')
			appconfig.set('files', 'last_dir', os.path.dirname(filename))
			appconfig.set('files', 'last_file', os.path.basename(filename))
		dlg.Destroy()

	def _on_menu_file_sync(self, _evt):
		appconfig = AppConfig()
		last_sync_file = appconfig.get('files', 'last_sync_file')
		if not last_sync_file:
			dlg = wx.FileDialog(self.wnd,
					defaultDir=appconfig.get('files', 'last_dir', ''),
					defaultFile=appconfig.get('files', 'last_file', 'GTD_SYNC.zip'),
					style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
			if dlg.ShowModal() == wx.ID_OK:
				last_sync_file = dlg.GetPath()
			dlg.Destroy()
		if last_sync_file:
			appconfig.set('files', 'last_sync_file', last_sync_file)
			dlg = DlgSyncProggress(self.wnd)
			dlg.run()
			try:
				sync.sync(last_sync_file)
			except sync.SyncLockedError:
				msgbox = wx.MessageDialog(dlg.wnd, _("Sync file is locked."),
						_("wxGTD"), wx.OK | wx.ICON_HAND)
				msgbox.ShowModal()
				msgbox.Destroy()
			dlg.mark_finished()
			self._filter_tree_ctrl.RefreshItems()
			Publisher.sendMessage('task.update')

	def _on_menu_file_preferences(self, evt):
		if DlgPreferences(self.wnd).run(True):
			self._filter_tree_ctrl.RefreshItems()

	def _on_menu_file_exit(self, _evt):
		self.wnd.Close()

	def _on_btn_new_task(self, _evt):
		self._new_task()

	def _on_menu_help_about(self, _evt):
		""" Show about dialog """
		dlg_about.show_about_box(self.wnd)

	def _on_menu_task_new(self, _evt):
		self._new_task()

	def _on_menu_task_delete(self, _evt):
		self._delete_selected_task()

	def _on_menu_task_edit(self, _evt):
		self._edit_selected_task()

	def _on_menu_sett_tags(self, _evt):
		DlgTags(self.wnd).run(True)
		self._filter_tree_ctrl.RefreshItems()

	def _on_menu_sett_goals(self, _evt):
		DlgGoals(self.wnd).run(True)
		self._filter_tree_ctrl.RefreshItems()

	def _on_menu_sett_folders(self, _evt):
		DlgFolders(self.wnd).run(True)
		self._filter_tree_ctrl.RefreshItems()

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
		task_uuid, task_type = self._items_list_ctrl.items[evt.GetData()]
		if task_type in (enums.TYPE_PROJECT, enums.TYPE_CHECKLIST):
			session = self._session
			task = session.query(OBJ.Task).filter_by(uuid=task_uuid).first()
			self._items_path.append(task)
			self._refresh_list()
			return
		if not task_uuid:
			return
		if task_type == enums.TYPE_CHECKLIST_ITEM:
			dlg = DlgChecklistitem.create(task_uuid, self.wnd, task_uuid)
		else:
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

	def _on_btn_edit_selected_task(self, _evt):
		self._edit_selected_task()

	def _on_btn_delete_selected_task(self, _evt):
		self._delete_selected_task()

	def _on_btn_complete_task(self, _evt):
		task_uuid, _task_type = self._items_list_ctrl.get_item_info(None)
		if task_uuid is None:  # not selected
			return
		session = self._session
		task = session.query(OBJ.Task).filter_by(uuid=task_uuid).first()
		if not task.task_completed:
			if not logic.complete_task(task, self.wnd, session):
				return
		else:
			task.task_completed = False
		session.commit()
		self._refresh_list()

	def _on_btn_edit_parent(self, _evt):
		if not self._items_path:
			return
		task_uuid = self._items_path[-1].uuid
		if task_uuid:
			dlg = DlgTask.create(task_uuid, self.wnd, task_uuid)
			dlg.run()

	# logic

	def _refresh_list(self):
		group_id = self['rb_show_selection'].GetSelection()
		tmodel = self._filter_tree_ctrl.model
		params = {'starred': False, 'finished': None, 'min_priority': None,
				'max_due_date': None, 'tags': None, 'types': None}
		params['contexts'] = list(tmodel.checked_items_by_parent("CONTEXTS"))
		params['folders'] = list(tmodel.checked_items_by_parent("FOLDERS"))
		params['goals'] = list(tmodel.checked_items_by_parent("GOALS"))
		params['statuses'] = list(tmodel.checked_items_by_parent("STATUSES"))
		params['parent_uuid'] = parent = self._items_path[-1].uuid \
				if self._items_path else None
		params['tags'] = list(tmodel.checked_items_by_parent("TAGS"))
		if not self._btn_show_finished.GetValue():
			params['finished'] = False
		params['hide_until'] = self._btn_hide_until.GetValue()
		if not parent:
			if not self._btn_show_subtasks.GetValue():
				# tylko nadrzędne
				params['parent_uuid'] = 0
		if group_id == 0:  # all
			pass
		elif group_id == 1:  # hot
			if not params['parent_uuid']:
				# ignore hotlist settings when showing subtasks
				_get_hotlist_settings(params)
		elif group_id == 2:  # stared
			if not params['parent_uuid']:
				# ignore starred when showing subtasks
				params['starred'] = True
		elif group_id == 3:  # basket
			# no status, no context
			params['contexts'] = [None]
			params['statuses'] = [None]
		elif group_id == 4:  # finished
			params['finished'] = True
		elif group_id == 5:  # projects
			if not parent:
				params['types'] = [enums.TYPE_PROJECT]
		elif group_id == 6:  # checklists
			if parent:
				params['types'] = [enums.TYPE_CHECKLIST, enums.TYPE_CHECKLIST_ITEM]
			else:
				params['types'] = [enums.TYPE_CHECKLIST]
		_LOG.debug("FrameMain._refresh_list; params=%r", params)
		wx.SetCursor(wx.HOURGLASS_CURSOR)
		tasks = OBJ.Task.select_by_filters(params, session=self._session)
		items_list = self._items_list_ctrl
		active_only = not self._btn_show_finished.GetValue()
		self._items_list_ctrl.fill(tasks, active_only=active_only)
		self.wnd.SetStatusText(_("Showed %d items") % items_list.GetItemCount())
		#path_str = ' / '.join(task.title for task in self._items_path)
		self._show_parent_info(active_only)
		wx.SetCursor(wx.STANDARD_CURSOR)

	def _autosync(self):
		appconfig = AppConfig()
		last_sync_file = appconfig.get('files', 'last_sync_file')
		if last_sync_file:
			dlg = DlgSyncProggress(self.wnd)
			dlg.run()
			try:
				sync.sync(last_sync_file)
			except sync.SyncLockedError:
				msgbox = wx.MessageDialog(dlg.wnd, _("Sync file is locked."),
						_("wxGTD"), wx.OK | wx.ICON_HAND)
				msgbox.ShowModal()
				msgbox.Destroy()
			dlg.mark_finished(2)
			self._filter_tree_ctrl.RefreshItems()
			Publisher.sendMessage('task.update')

	def _delete_selected_task(self):
		task_uuid, _task_type = self._items_list_ctrl.get_item_info(None)
		if task_uuid:
			if logic.delete_task(task_uuid, self.wnd):
				Publisher.sendMessage('task.delete', data={'task_uuid': task_uuid})

	def _new_task(self):
		parent_uuid = None
		if self._items_path:
			parent_uuid = self._items_path[-1].uuid
			if self._items_path[-1].type == enums.TYPE_CHECKLIST:
				dlg = DlgChecklistitem(self.wnd, None, parent_uuid)
				dlg.run()
				return
		group_id = self['rb_show_selection'].GetSelection()
		task_type = enums.TYPE_TASK
		if group_id == 5:
			task_type = enums.TYPE_PROJECT
		elif group_id == 6:
			task_type = enums.TYPE_CHECKLIST
		dlg = DlgTask(self.wnd, None, parent_uuid, task_type)
		dlg.run()

	def _edit_selected_task(self):
		task_uuid, _task_type = self._items_list_ctrl.get_item_info(None)
		if task_uuid:
			dlg = DlgTask.create(task_uuid, self.wnd, task_uuid)
			dlg.run()

	def _show_parent_info(self, active_only):
		if not self._items_path:
			self['l_parent_title'].SetLabel('')
			self['l_parent_info'].SetLabel('')
			self['l_parent_due'].SetLabel('')
			self['l_parent_tags'].SetLabel('')
			self.wnd.FindWindowById(wx.ID_UP).Enable(False)
			self['btn_parent_edit'].Enable(False)
			return
		self['btn_parent_edit'].Enable(True)
		self.wnd.FindWindowById(wx.ID_UP).Enable(True)
		parent = self._items_path[-1]
		self['l_parent_title'].SetLabel(parent.title or '')
		self['l_parent_info'].SetLabel(fmt.format_task_info(parent) or '')
		self['l_parent_due'].SetLabel(fmt.format_timestamp(parent.due_date,
				parent.due_time_set).replace(' ', '\n'))
		self['l_parent_tags'].SetLabel(fmt.format_task_info_icons(parent,
				active_only)[0])
		self['panel_parent'].GetSizer().Layout()


def _update_color(wnd, bgcolor):
	for child in wnd.GetChildren():
		if isinstance(child, wx.Panel):
			child.SetBackgroundColour(bgcolor)
		_update_color(child, bgcolor)


def _get_hotlist_settings(params):
	now = datetime.datetime.now()
	conf = AppConfig()
	params['filter_operator'] = 'or' if conf.get('hotlist', 'cond', True) \
			else 'and'
	params['max_due_date'] = now + datetime.timedelta(days=conf.get('hotlist',
			'due', 0))
	params['min_priority'] = conf.get('hotlist', 'priority', 3)
	params['starred'] = conf.get('hotlist', 'starred', False)
	params['next_action'] = conf.get('hotlist', 'next_action', False)
	params['started'] = conf.get('hotlist', 'started', False)
	print params
