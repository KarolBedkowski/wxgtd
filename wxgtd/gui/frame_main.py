# -*- coding: utf-8 -*-
""" Main application window.

Copyright (c) Karol Będkowski, 2013

This file is part of wxGTD
Licence: GPLv2+
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2013"
__version__ = "2013-04-28"

import sys
import os
import gettext
import logging
import traceback

import wx
import wx.lib.customtreectrl as CT
import wx.lib.dialogs
try:
	from wx.lib.pubsub.pub import Publisher
except ImportError:
	from wx.lib.pubsub import Publisher  # pylint: disable=E0611

from wxgtd.wxtools import iconprovider
from wxgtd.model import objects as OBJ
from wxgtd.model import loader
from wxgtd.model import exporter
from wxgtd.model import sync
from wxgtd.model import enums
from wxgtd.model import queries
from wxgtd.logic import task as task_logic
from wxgtd.lib import fmt
from wxgtd.gui import dlg_about
from wxgtd.gui import _infobox as infobox
from wxgtd.gui import message_boxes as mbox
from wxgtd.gui import _tasklistctrl as TLC
from wxgtd.gui import quicktask
from wxgtd.gui._base_frame import BaseFrame
from wxgtd.gui._filtertreectrl import FilterTreeCtrl
from wxgtd.gui._taskbaricon import TaskBarIcon
from wxgtd.gui.dlg_preferences import DlgPreferences
from wxgtd.gui.dlg_sync_progress import DlgSyncProggress
from wxgtd.gui.dlg_tags import DlgTags
from wxgtd.gui.dlg_goals import DlgGoals
from wxgtd.gui.dlg_folders import DlgFolders
from wxgtd.gui.dlg_contexts import DlgContexts
from wxgtd.gui.dlg_export_tasks import DlgExportTasks
from wxgtd.gui.frame_reminders import FrameReminders
from wxgtd.gui.frame_notebooks import FrameNotebook
from wxgtd.gui.task_controller import TaskController
from wxgtd.gui.frame_search import FrameSeach

_ = gettext.gettext
ngettext = gettext.ngettext  # pylint: disable=C0103
_LOG = logging.getLogger(__name__)


class FrameMain(BaseFrame):
	""" Main window class. """
	# pylint: disable=R0903, R0902

	_xrc_resource = 'wxgtd.xrc'
	_window_name = 'frame_main'
	_window_icon = 'wxgtd'

	def __init__(self):
		self._all_loaded = False
		BaseFrame.__init__(self)
		self._setup()
		wx.CallAfter(self._on_all_loaded)

	def _setup(self):
		self._session = OBJ.Session()
		self._items_path = []
		self._last_reminders_check = None
		self._filter_tree_ctrl.RefreshItems()
		self._tbicon = TaskBarIcon(self.wnd)  # pylint: disable=W0201
		self['rb_show_selection'].SetSelection(self._appconfig.get('main',
			'selected_group', 0))
		if self._appconfig.get('sync', 'sync_on_startup'):
			wx.CallAfter(self._autosync)
		self._reminders_timer = wx.Timer(self.wnd)
		self._reminders_timer.Start(30 * 1000)  # 30 sec

	def _load_controls(self):
		# pylint: disable=W0201
		# filter tree ctrl
		filter_tree_panel = self['filter_tree_panel']
		box = wx.BoxSizer(wx.HORIZONTAL)
		self._filter_tree_ctrl = FilterTreeCtrl(filter_tree_panel, -1)
		box.Add(self._filter_tree_ctrl, 1, wx.EXPAND)
		filter_tree_panel.SetSizer(box)
		# tasklist
		tasklist_panel = self['tasklist_panel']
		box = wx.BoxSizer(wx.HORIZONTAL)
		self._items_list_ctrl = TLC.TaskListControl(tasklist_panel)
		box.Add(self._items_list_ctrl, 1, wx.EXPAND)
		tasklist_panel.SetSizer(box)
		ppinfo = self['panel_parent_info']
		self._panel_parent_info = infobox.TaskInfoPanel(ppinfo, -1)
		box = wx.BoxSizer(wx.HORIZONTAL)
		box.Add(self._panel_parent_info, 1, wx.EXPAND)
		ppinfo.SetSizer(box)
		ppicons = self['panel_parent_icons']
		self._panel_parent_icons = infobox.TaskIconsPanel(ppicons, -1)
		box = wx.BoxSizer(wx.HORIZONTAL)
		box.Add(self._panel_parent_icons, 1, wx.EXPAND)
		ppicons.SetSizer(box)
		self._tasks_popup_menu = _TasksPopupMenu()

	def _create_bindings(self, wnd):
		BaseFrame._create_bindings(self, wnd)

		self._create_menu_bind('menu_file_load', self._on_menu_file_load)
		self._create_menu_bind('menu_file_save', self._on_menu_file_save)
		self._create_menu_bind('menu_file_exit', self._on_menu_file_exit)
		self._create_menu_bind('menu_file_sync', self._on_menu_file_sync)
		self._create_menu_bind('menu_file_export_tasks',
				self._on_menu_file_export_tasks)
		self._create_menu_bind('menu_help_about', self._on_menu_help_about)
		self._create_menu_bind('menu_task_new', self._on_menu_task_new)
		self._create_menu_bind('menu_task_quick', self._on_menu_task_quick)
		self._create_menu_bind('menu_task_edit', self._on_menu_task_edit)
		self._create_menu_bind('menu_task_delete', self._on_menu_task_delete)
		self._create_menu_bind('menu_task_clone', self._on_menu_task_clone)
		self._create_menu_bind('menu_notebook_open', self._on_menu_notebook_open)
		self._create_menu_bind('menu_task_complete', self._on_menu_task_complete)
		self._create_menu_bind('menu_task_starred', self._on_menu_task_starred)
		self._create_menu_bind('menu_search_task', self._on_menu_search_task)
		self._create_menu_bind('menu_sett_tags', self._on_menu_sett_tags)
		self._create_menu_bind('menu_sett_goals', self._on_menu_sett_goals)
		self._create_menu_bind('menu_sett_folders', self._on_menu_sett_folders)
		self._create_menu_bind('menu_sett_contexts', self._on_menu_sett_contexts)
		self._create_menu_bind('menu_sett_preferences',
				self._on_menu_sett_preferences)

		wnd.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self._on_filter_tree_item_activated,
				self._filter_tree_ctrl)
		wnd.Bind(CT.EVT_TREE_ITEM_CHECKED, self._on_filter_tree_item_selected,
				self._filter_tree_ctrl)
		wnd.Bind(wx.EVT_RADIOBOX, self._on_rb_show_selection,
				self['rb_show_selection'])
		wnd.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self._on_items_list_activated,
				self._items_list_ctrl)
		self._items_list_ctrl.Bind(wx.EVT_COMMAND_RIGHT_CLICK,
				self._on_items_list_right_click)
		self._items_list_ctrl.Bind(wx.EVT_RIGHT_UP,
				self._on_items_list_right_click)
		self._items_list_ctrl.Bind(TLC.EVT_DRAG_TASK, self._on_item_drag)
		wnd.Bind(wx.EVT_BUTTON, self._on_btn_path_back, id=wx.ID_UP)
		wnd.Bind(wx.EVT_BUTTON, self._on_btn_edit_parent,
				self['btn_parent_edit'])
		wnd.Bind(wx.EVT_TIMER, self._on_timer)
		wnd.Bind(wx.EVT_ICONIZE, self._on_window_iconze)

		Publisher().subscribe(self._on_tasks_update, ('task', 'update'))
		Publisher().subscribe(self._on_tasks_update, ('task', 'delete'))

		self._create_popup_menu_bindings(wnd)

	def _create_popup_menu_bindings(self, wnd):
		wnd.Bind(wx.EVT_MENU, self._on_menu_task_edit,
				id=self._tasks_popup_menu.task_edit_id)
		wnd.Bind(wx.EVT_MENU, self._on_menu_task_delete,
				id=self._tasks_popup_menu.task_delete_id)
		wnd.Bind(wx.EVT_MENU, self._on_menu_task_toggle_completed,
				id=self._tasks_popup_menu.toggle_task_complete_id)
		wnd.Bind(wx.EVT_MENU, self._on_menu_task_set_completed,
				id=self._tasks_popup_menu.task_set_complete_id)
		wnd.Bind(wx.EVT_MENU, self._on_menu_task_set_not_completed,
				id=self._tasks_popup_menu.task_set_not_complete_id)
		wnd.Bind(wx.EVT_MENU, self._on_menu_task_toggle_starred,
				id=self._tasks_popup_menu.toggle_task_stared_id)
		wnd.Bind(wx.EVT_MENU, self._on_menu_task_set_starred,
				id=self._tasks_popup_menu.task_set_starred_id)
		wnd.Bind(wx.EVT_MENU, self._on_menu_task_set_not_starred,
				id=self._tasks_popup_menu.task_set_not_starred_id)
		wnd.Bind(wx.EVT_MENU, self._on_menu_task_clone,
				id=self._tasks_popup_menu.task_clone_id)
		wnd.Bind(wx.EVT_MENU, self._on_menu_task_change_due,
				id=self._tasks_popup_menu.task_change_due_id)
		wnd.Bind(wx.EVT_MENU, self._on_menu_task_change_start,
				id=self._tasks_popup_menu.task_change_start_id)
		wnd.Bind(wx.EVT_MENU, self._on_menu_task_change_remind,
				id=self._tasks_popup_menu.task_change_remind_id)
		wnd.Bind(wx.EVT_MENU, self._on_menu_task_change_hide_until,
				id=self._tasks_popup_menu.task_change_hide_until_id)
		wnd.Bind(wx.EVT_MENU, self._on_menu_task_change_context,
				id=self._tasks_popup_menu.task_change_context_id)
		wnd.Bind(wx.EVT_MENU, self._on_menu_task_change_folder,
				id=self._tasks_popup_menu.task_change_folder_id)
		wnd.Bind(wx.EVT_MENU, self._on_menu_task_change_project,
				id=self._tasks_popup_menu.task_change_project_id)
		wnd.Bind(wx.EVT_MENU, self._on_menu_task_change_status,
				id=self._tasks_popup_menu.task_change_status_id)
		wnd.Bind(wx.EVT_MENU, self._on_menu_task_change_priority,
				id=self._tasks_popup_menu.task_change_priority_id)

	def _create_toolbar(self):
		toolbar = self.wnd.CreateToolBar()
		tbi = toolbar.AddLabelTool(-1, _('New Task'),
				iconprovider.get_image("task_new"),
				shortHelp=_('Add new task'))
		self.wnd.Bind(wx.EVT_TOOL, self._on_btn_new_task, id=tbi.GetId())

		tbi = toolbar.AddLabelTool(-1, _('Quick Task'),
				iconprovider.get_image("task_quick"),
				shortHelp=_('Add quick new task'))
		self.wnd.Bind(wx.EVT_TOOL, self._on_btn_quick_task, id=tbi.GetId())

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

		tbi = toolbar.AddLabelTool(-1, _('Toggle Task Starred'),
				iconprovider.get_image('task_starred'),
				shortHelp=_('Toggle selected task starred'))
		self.wnd.Bind(wx.EVT_TOOL, self._on_btn_starred_task, id=tbi.GetId())

		toolbar.AddSeparator()

		appconfig = self._appconfig

		# show subtask
		self._btn_show_subtasks = wx.ToggleButton(toolbar,  # pylint: disable=W0201
				-1, _(" Show subtasks "))
		toolbar.AddControl(self._btn_show_subtasks)
		self.wnd.Bind(wx.EVT_TOGGLEBUTTON, self._on_btn_show_subtasks,
				self._btn_show_subtasks)
		self._btn_show_subtasks.SetValue(appconfig.get('main', 'show_subtask', True))

		toolbar.AddControl(wx.StaticText(toolbar, -1, " "))

		# show completed
		self._btn_show_finished = wx.ToggleButton(toolbar,  # pylint: disable=W0201
				-1, _(" Show finished "))
		toolbar.AddControl(self._btn_show_finished)
		self.wnd.Bind(wx.EVT_TOGGLEBUTTON, self._on_btn_show_finished,
				self._btn_show_finished)
		self._btn_show_finished.SetValue(appconfig.get('main', 'show_finished',
				False))

		toolbar.AddControl(wx.StaticText(toolbar, -1, " "))

		# hide until due
		self._btn_hide_until = wx.ToggleButton(toolbar,  # pylint: disable=W0201
				-1, _(" Hide until "))
		toolbar.AddControl(self._btn_hide_until)
		self.wnd.Bind(wx.EVT_TOGGLEBUTTON, self._on_btn_hide_due,
				self._btn_hide_until)
		self._btn_hide_until.SetValue(appconfig.get('main', 'show_hide_until', True))

		toolbar.AddSeparator()

		tbi = toolbar.AddLabelTool(-1, _('Synchronize tasks'),
				iconprovider.get_image('sync'))
		self.wnd.Bind(wx.EVT_TOOL, self._on_menu_file_sync, id=tbi.GetId())

		toolbar.AddSeparator()

		# search box
		self._searchbox = wx.SearchCtrl(toolbar, -1,  # pylint: disable=W0201
				size=(150, -1), style=wx.TE_PROCESS_ENTER)
		self._searchbox.SetDescriptiveText(_('Search'))
		self._searchbox.ShowCancelButton(True)
		toolbar.AddControl(self._searchbox)
		#self.wnd.Bind(wx.EVT_TEXT, self._on_search, self._searchbox)
		self.wnd.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN, self._on_search,
				self._searchbox)
		self.wnd.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self._on_search_cancel,
				self._searchbox)
		self.wnd.Bind(wx.EVT_TEXT_ENTER, self._on_search, self._searchbox)

		toolbar.AddSeparator()

		tbi = toolbar.AddLabelTool(-1, _('Reminders'),
				iconprovider.get_image('reminders'))
		self.wnd.Bind(wx.EVT_TOOL, self._on_btn_reminders, id=tbi.GetId())

		tbi = toolbar.AddLabelTool(-1, _('Notebook'),
				iconprovider.get_image('notebook'))
		self.wnd.Bind(wx.EVT_TOOL, self._on_menu_notebook_open, id=tbi.GetId())

		tbi = toolbar.AddLabelTool(-1, _('Search'),
				iconprovider.get_image(wx.ART_FIND))
		self.wnd.Bind(wx.EVT_TOOL, self._on_menu_search_task, id=tbi.GetId())

		toolbar.Realize()

	# events

	def _on_all_loaded(self):
		self._all_loaded = True
		self._refresh_list()

	def _on_close(self, event):
		appconfig = self._appconfig
		if appconfig.get('sync', 'sync_on_exit'):
			self._autosync(False)
		appconfig.set('main', 'show_finished', self._btn_show_finished.GetValue())
		appconfig.set('main', 'show_subtask', self._btn_show_subtasks.GetValue())
		appconfig.set('main', 'show_hide_until', self._btn_hide_until.GetValue())
		appconfig.set('main', 'selected_group',
				self['rb_show_selection'].GetSelection())
		self._filter_tree_ctrl.save_last_settings()
		self._tbicon.Destroy()
		BaseFrame._on_close(self, event)

	def _on_menu_file_load(self, _evt):
		appconfig = self._appconfig
		dlg = wx.FileDialog(self.wnd,
				_("Please select sync file."),
				defaultDir=appconfig.get('files', 'last_dir', ''),
				defaultFile=appconfig.get('files', 'last_file', 'GTD_SYNC.zip'),
				style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
		if dlg.ShowModal() == wx.ID_OK:
			filename = dlg.GetPath()
			dlgp = DlgSyncProggress(self.wnd)
			dlgp.run()
			try:
				loader.load_from_file(filename, dlgp.update, force=True)
			except Exception as err:  # pylint: disable=W0703
				error = "\n".join(traceback.format_exception(*sys.exc_info()))
				msgdlg = wx.lib.dialogs.ScrolledMessageDialog(self.wnd,
						str(err) + "\n\n" + error, _("Synchronisation error"))
				msgdlg.ShowModal()
				msgdlg.Destroy()
			dlgp.mark_finished(2)
			appconfig.set('files', 'last_dir', os.path.dirname(filename))
			appconfig.set('files', 'last_file', os.path.basename(filename))
			Publisher().sendMessage('task.update')
		dlg.Destroy()

	def _on_menu_file_save(self, _evt):
		appconfig = self._appconfig
		dlg = wx.FileDialog(self.wnd,
				_("Please select target sync file."),
				defaultDir=appconfig.get('files', 'last_dir', ''),
				defaultFile=appconfig.get('files', 'last_file', 'GTD_SYNC.zip'),
				style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
		if dlg.ShowModal() == wx.ID_OK:
			filename = dlg.GetPath()
			dlgp = DlgSyncProggress(self.wnd)
			dlgp.run()
			try:
				exporter.save_to_file(filename, dlgp.update)
			except Exception as err:  # pylint: disable=W0703
				error = "\n".join(traceback.format_exception(*sys.exc_info()))
				msgdlg = wx.lib.dialogs.ScrolledMessageDialog(self.wnd,
						str(err) + "\n\n" + error, _("Synchronisation error"))
				msgdlg.ShowModal()
				msgdlg.Destroy()
			dlgp.mark_finished(2)
			Publisher().sendMessage('task.update')
			appconfig.set('files', 'last_dir', os.path.dirname(filename))
			appconfig.set('files', 'last_file', os.path.basename(filename))
		dlg.Destroy()

	def _on_menu_file_sync(self, _evt):
		appconfig = self._appconfig
		last_sync_file = appconfig.get('files', 'last_sync_file')
		if not last_sync_file:
			dlg = wx.FileDialog(self.wnd,
					_("Please select sync file."),
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
			except sync.OtherSyncError as err:
				error = "\n".join(traceback.format_exception(*sys.exc_info()))
				msgdlg = wx.lib.dialogs.ScrolledMessageDialog(self.wnd,
						str(err) + "\n\n" + error, _("Synchronisation error"))
				msgdlg.ShowModal()
				msgdlg.Destroy()
			dlg.mark_finished()
			self._filter_tree_ctrl.RefreshItems()
			Publisher().sendMessage('task.update')
			Publisher().sendMessage('dict.update')

	def _on_menu_sett_preferences(self, _evt):
		if DlgPreferences(self.wnd).run(True):
			self._filter_tree_ctrl.RefreshItems()

	def _on_menu_file_export_tasks(self, _evt):
		params = self._get_params_for_list()
		tasks = OBJ.Task.select_by_filters(params, session=self._session)
		if tasks:
			DlgExportTasks(self.wnd, tasks).run(modal=True)

	def _on_menu_file_exit(self, _evt):
		self.wnd.Close()

	def _on_btn_new_task(self, _evt):
		self._new_task()

	def _on_btn_quick_task(self, _evt):
		quicktask.quick_task(self.wnd)

	def _on_menu_help_about(self, _evt):
		""" Show about dialog """
		dlg_about.show_about_box(self.wnd)

	def _on_menu_task_new(self, _evt):
		self._new_task()

	def _on_menu_task_quick(self, _evt):
		quicktask.quick_task(self.wnd)

	def _on_menu_task_delete(self, _evt):
		self._delete_selected_task()

	def _on_menu_task_edit(self, _evt):
		self._edit_selected_task()

	def _on_menu_task_clone(self, _evt):
		self._clone_selected_task()

	def _on_menu_task_toggle_completed(self, _evt):
		self._toggle_task_complete()

	def _on_menu_task_set_completed(self, _evt):
		tasks_uuid = list(self._items_list_ctrl.get_selected_items_uuid())
		if tasks_uuid:
			TaskController(self.wnd, self._session,
					None).tasks_set_completed_status(tasks_uuid, True)

	def _on_menu_task_set_not_completed(self, _evt):
		tasks_uuid = list(self._items_list_ctrl.get_selected_items_uuid())
		if tasks_uuid:
			TaskController(self.wnd, self._session,
					None).tasks_set_completed_status(tasks_uuid, False)

	def _on_menu_task_toggle_starred(self, _evt):
		self._toggle_task_starred()

	def _on_menu_task_set_starred(self, _evt):
		tasks_uuid = list(self._items_list_ctrl.get_selected_items_uuid())
		TaskController(self.wnd, self._session,
				None).tasks_set_starred_flag(tasks_uuid, True)

	def _on_menu_task_set_not_starred(self, _evt):
		tasks_uuid = list(self._items_list_ctrl.get_selected_items_uuid())
		TaskController(self.wnd, self._session,
				None).tasks_set_starred_flag(tasks_uuid, False)

	def _on_menu_task_change_due(self, _evt):
		if self._items_list_ctrl.selected_count == 1:
			task = self._get_selected_task()
			if task and TaskController(self.wnd, self._session, task).\
					task_change_due_date():
				task_logic.save_modified_task(task, self._session)
		elif self._items_list_ctrl.selected_count > 1:
			tasks_uuid = list(self._items_list_ctrl.get_selected_items_uuid())
			TaskController(self.wnd, self._session,
					None).tasks_change_due_date(tasks_uuid)

	def _on_menu_task_change_start(self, _evt):
		if self._items_list_ctrl.selected_count == 1:
			task = self._get_selected_task()
			if (task and TaskController(self.wnd, self._session, task).
					task_change_start_date()):
				task_logic.save_modified_task(task, self._session)
		elif self._items_list_ctrl.selected_count > 1:
			tasks_uuid = list(self._items_list_ctrl.get_selected_items_uuid())
			TaskController(self.wnd, self._session,
					None).tasks_change_start_date(tasks_uuid)

	def _on_menu_task_change_remind(self, _evt):
		if self._items_list_ctrl.selected_count == 1:
			task = self._get_selected_task()
			if task and TaskController(self.wnd, self._session, task).\
					task_change_remind():
				task_logic.save_modified_task(task, self._session)
		elif self._items_list_ctrl.selected_count > 1:
			tasks_uuid = list(self._items_list_ctrl.get_selected_items_uuid())
			TaskController(self.wnd, self._session,
					None).tasks_change_remind(tasks_uuid)

	def _on_menu_task_change_hide_until(self, _evt):
		if self._items_list_ctrl.selected_count == 1:
			task = self._get_selected_task()
			if task and TaskController(self.wnd, self._session, task).\
					task_change_hide_until():
				task_logic.save_modified_task(task, self._session)
		elif self._items_list_ctrl.selected_count > 1:
			tasks_uuid = list(self._items_list_ctrl.get_selected_items_uuid())
			TaskController(self.wnd, self._session,
					None).tasks_change_hide_until(tasks_uuid)

	def _on_menu_task_change_context(self, _evt):
		tasks_uuid = list(self._items_list_ctrl.get_selected_items_uuid())
		if tasks_uuid:
			TaskController(self.wnd, self._session,
					None).tasks_change_context(tasks_uuid)

	def _on_menu_task_change_folder(self, _evt):
		tasks_uuid = list(self._items_list_ctrl.get_selected_items_uuid())
		if tasks_uuid:
			TaskController(self.wnd, self._session,
					None).tasks_change_folder(tasks_uuid)

	def _on_menu_task_change_project(self, _evt):
		tasks_uuid = list(self._items_list_ctrl.get_selected_items_uuid())
		if tasks_uuid:
			TaskController(self.wnd, self._session,
					None).tasks_change_project(tasks_uuid)

	def _on_menu_task_change_status(self, _evt):
		tasks_uuid = list(self._items_list_ctrl.get_selected_items_uuid())
		if tasks_uuid:
			TaskController(self.wnd, self._session,
					None).tasks_change_status(tasks_uuid)

	def _on_menu_task_change_priority(self, _evt):
		tasks_uuid = list(self._items_list_ctrl.get_selected_items_uuid())
		if tasks_uuid:
			TaskController(self.wnd, self._session,
					None).tasks_change_priority(tasks_uuid)

	def _on_menu_task_complete(self, _evt):
		self._toggle_task_complete()

	def _on_menu_task_starred(self, _evt):
		self._toggle_task_starred()

	def _on_menu_search_task(self, _evt):
		FrameSeach.run(self.wnd)

	def _on_menu_notebook_open(self, _evt):  # pylint: disable=R0201
		FrameNotebook.run()

	def _on_menu_sett_tags(self, _evt):
		DlgTags(self.wnd).run(True)
		self._filter_tree_ctrl.RefreshItems()

	def _on_menu_sett_goals(self, _evt):
		DlgGoals(self.wnd).run(True)
		self._filter_tree_ctrl.RefreshItems()

	def _on_menu_sett_folders(self, _evt):
		DlgFolders(self.wnd).run(True)
		self._filter_tree_ctrl.RefreshItems()

	def _on_menu_sett_contexts(self, _evt):
		DlgContexts(self.wnd).run(True)
		self._filter_tree_ctrl.RefreshItems()

	def _on_filter_tree_item_activated(self, evt):
		self._refresh_list()
		evt.Skip()

	def _on_filter_tree_item_selected(self, evt):
		self._refresh_list()
		evt.Skip()

	def _on_rb_show_selection(self, evt):
		self._refresh_list()
		evt.Skip()

	def _on_items_list_activated(self, evt):
		task_uuid, task_type = self._items_list_ctrl.items[evt.GetData()]
		if task_type in (enums.TYPE_PROJECT, enums.TYPE_CHECKLIST):
			task = OBJ.Task.get(self._session, uuid=task_uuid)
			self._items_path.append(task)
			self._refresh_list()
			return
		if task_uuid:
			TaskController.open_task(self.wnd, task_uuid)

	def _on_item_drag(self, evt):
		s_index = evt.start
		e_index = evt.stop
		_LOG.debug('FrameMain._on_item_drag: %r -> %r', s_index, e_index)
		if s_index == e_index:
			return
		items = []
		if s_index < e_index:
			for idx in xrange(s_index, e_index):
				items.append(OBJ.Task.get(self._session,
						uuid=self._items_list_ctrl.get_item_uuid(idx)))
			items.append(items.pop(0))
		else:
			for idx in xrange(e_index, s_index + 1):
				items.append(OBJ.Task.get(self._session,
						uuid=self._items_list_ctrl.get_item_uuid(idx)))
			items.insert(0, items.pop(-1))
		first_importance = min(item.importance for item in items)
		for idx, item in enumerate(items):
			item.importance = first_importance + idx
			item.update_modify_time()
		self._session.commit()
		self._refresh_list()

	def _on_items_list_right_click(self, _evt):
		if self._items_list_ctrl.selected_count == 0:
			return
		elif self._items_list_ctrl.selected_count == 1:
			task_uuid = self._items_list_ctrl.get_item_uuid(None)
			task = OBJ.Task.get(session=self._session, uuid=task_uuid)
			menu = self._tasks_popup_menu.build(task)
		else:
			menu = self._tasks_popup_menu.build_multi(set(
				self._items_list_ctrl.get_selected_items_type()))
		self.wnd.PopupMenu(menu)
		menu.Destroy()

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
		self._toggle_task_complete()

	def _on_btn_starred_task(self, _evt):
		self._toggle_task_starred()

	def _on_btn_edit_parent(self, _evt):
		if self._items_path:
			task_uuid = self._items_path[-1].uuid
			if task_uuid:
				TaskController.open_task(self.wnd, task_uuid)

	def _on_btn_reminders(self, _evt):
		if not FrameReminders.check(self.wnd, self._session):
			mbox.message_box_info(self.wnd, _("No active alarms in this moment."),
					_("Alarms"))

	def _on_search(self, _evt):
		self._refresh_list()

	def _on_search_cancel(self, _evt):
		if self._searchbox.GetValue():
			self._searchbox.SetValue('')
			self._refresh_list()

	def _on_timer(self, _evt, _force_show=False):
		if self._appconfig.get('notification', 'popup_alarms'):
			_LOG.debug('FrameMain._on_timer: check reminders')
			FrameReminders.check(self.wnd, self._session)

	def _on_window_iconze(self, _evt):
		if self._appconfig.get('gui', 'min_to_tray'):
			self.wnd.Show(False)

	def _refresh_list(self):
		if not self._all_loaded:
			return
		wx.SetCursor(wx.HOURGLASS_CURSOR)
		self.wnd.Freeze()
		params = self._get_params_for_list()
		_LOG.debug("FrameMain._refresh_list; params=%r", params)
		self._session.expire_all()  # pylint: disable=E1101
		tasks = OBJ.Task.select_by_filters(params, session=self._session)
		active_only = params['finished'] is not None and not params['finished']
		self._items_list_ctrl.fill(tasks, active_only=active_only)
		showed = self._items_list_ctrl.GetItemCount()
		self.wnd.SetStatusText(ngettext("%d item", "%d items", showed) % showed, 1)
		self._show_parent_info(active_only)
		self._refresh_groups()
		self.wnd.Thaw()
		wx.SetCursor(wx.STANDARD_CURSOR)

	def _autosync(self, on_load=True):
		last_sync_file = self._appconfig.get('files', 'last_sync_file')
		if last_sync_file:
			dlg = DlgSyncProggress(self.wnd)
			dlg.run()
			try:
				sync.sync(last_sync_file, load_only=on_load)
			except sync.SyncLockedError:
				msgbox = wx.MessageDialog(dlg.wnd, _("Sync file is locked."),
						_("wxGTD"), wx.OK | wx.ICON_HAND)
				msgbox.ShowModal()
				msgbox.Destroy()
			dlg.mark_finished(2)
		if on_load:
			Publisher().sendMessage('task.update')
			Publisher().sendMessage('dict.update')

	def _delete_selected_task(self):
		tasks_uuid = list(self._items_list_ctrl.get_selected_items_uuid())
		if len(tasks_uuid) == 1:
			TaskController(self.wnd, self._session, tasks_uuid[0]).\
					delete_task()
		elif len(tasks_uuid) > 1:
			TaskController(self.wnd, self._session,
					None).delete_tasks(tasks_uuid)

	def _new_task(self):
		parent_uuid = None
		task_type = None
		if self._items_path:
			parent_uuid = self._items_path[-1].uuid
			if self._items_path[-1].type == enums.TYPE_CHECKLIST:
				task_type = enums.TYPE_CHECKLIST_ITEM
		if not task_type:
			group_id = self['rb_show_selection'].GetSelection()
			task_type = enums.TYPE_TASK
			if group_id == 5 and not self._items_path:
				task_type = enums.TYPE_PROJECT
			elif group_id == 6 and not self._items_path:
				task_type = enums.TYPE_CHECKLIST
		TaskController.new_task(self.wnd, task_type or enums.TYPE_TASK,
				parent_uuid)

	def _edit_selected_task(self):
		task_uuid = self._items_list_ctrl.get_item_uuid(None)
		if task_uuid:
			TaskController.open_task(self.wnd, task_uuid)

	def _clone_selected_task(self):
		task_uuid = self._items_list_ctrl.get_item_uuid(None)
		if not task_uuid:
			return
		if not mbox.message_box_question_yesno(self.wnd,
				_("Clone task with all subtasks?")):
			return
		task_logic.clone_task(task_uuid)

	def _show_parent_info(self, active_only):
		panel_parent_icons = self._panel_parent_icons
		panel_parent_info = self._panel_parent_info
		if not self._items_path:
			self['panel_parent'].SetBackgroundColour(
					self.wnd.GetBackgroundColour())
			self['btn_parent_edit'].Enable(False)
			self.wnd.FindWindowById(wx.ID_UP).Enable(False)
			panel_parent_info.set_task(None)
			panel_parent_icons.set_task(None)
			self['l_parent_due'].SetLabel("")
		else:
			self['panel_parent'].SetBackgroundColour(wx.WHITE)
			self['btn_parent_edit'].Enable(True)
			self.wnd.FindWindowById(wx.ID_UP).Enable(True)
			parent = self._items_path[-1]
			panel_parent_info.set_task(parent)
			panel_parent_icons.set_task(parent)
			if parent.type == enums.TYPE_PROJECT:
				self['l_parent_due'].SetLabel(fmt.format_timestamp(
					parent.due_date_project, parent.due_time_set).replace(' ', '\n'))
			else:
				self['l_parent_due'].SetLabel(fmt.format_timestamp(
					parent.due_date, parent.due_time_set).replace(' ', '\n'))
		panel_parent_icons.active_only = active_only
		panel_parent_info.Refresh()
		panel_parent_info.Update()
		panel_parent_icons.Refresh()
		panel_parent_icons.Update()
		self['panel_parent'].GetSizer().Layout()

	def _get_params_for_list(self, group=None, skip_search=False):
		""" Build params for database query """
		group_id = (self['rb_show_selection'].GetSelection() if group is None
				else group)
		parent = self._items_path[-1].uuid if self._items_path else None
		_LOG.debug('_get_params_for_list: group_id=%r, parent=%r', group_id, parent)
		tmodel = self._filter_tree_ctrl.model
		options = 0
		if self._btn_show_finished.GetValue():
			options |= queries.OPT_SHOW_FINISHED
		if self._btn_show_subtasks.GetValue():
			options |= queries.OPT_SHOW_SUBTASKS
		if self._btn_hide_until.GetValue():
			options |= queries.OPT_HIDE_UNTIL
		params = queries.build_query_params(group_id, options, parent,
				"" if skip_search else self._searchbox.GetValue())
		queries.query_params_append_contexts(params,
				tmodel.checked_items_by_parent("CONTEXTS"))
		queries.query_params_append_folders(params,
				tmodel.checked_items_by_parent("FOLDERS"))
		queries.query_params_append_goals(params,
				tmodel.checked_items_by_parent("GOALS"))
		queries.query_params_append_statuses(params,
				tmodel.checked_items_by_parent("STATUSES"))
		queries.query_params_append_tags(params,
				tmodel.checked_items_by_parent("TAGS"))
		return params

	def _toggle_task_complete(self):
		task = self._get_selected_task()
		if not task:
			return
		if not task.completed and not TaskController(
				self.wnd, self._session, task).confirm_set_task_complete():
			return
		task_logic.toggle_task_complete(task.uuid, self._session)

	def _toggle_task_starred(self):
		task_uuid = self._items_list_ctrl.get_item_uuid(None)
		task_logic.toggle_task_starred(task_uuid, self._session)

	def _get_selected_task(self):
		""" Return Task object for selected item. """
		task_uuid = self._items_list_ctrl.get_item_uuid(None)
		if task_uuid:
			return OBJ.Task.get(self._session, uuid=task_uuid)
		return None

	def _refresh_groups(self):
		rb_show_selection = self['rb_show_selection']
		for group, label in enumerate((_("All (%d)"), _("Hotlist (%d)"),
				_("Starred (%d)"), _("Basket (%d)"), _("Finished (%d)"),
				_("Projects (%d)"), _("Checklists (%d)"),
				_("Active Alarms (%d)"))):
			cnt = OBJ.Task.select_by_filters(self._get_params_for_list(group,
					True), session=self._session).count()
			rb_show_selection.SetItemLabel(group, label % cnt)


class _TasksPopupMenu:
	""" Popup menu for tasks list. """
	# pylint: disable=R0902,R0903

	def __init__(self):
		self.toggle_task_complete_id = wx.NewId()
		self.task_set_complete_id = wx.NewId()
		self.task_set_not_complete_id = wx.NewId()
		self.task_edit_id = wx.NewId()
		self.task_clone_id = wx.NewId()
		self.task_delete_id = wx.NewId()
		self.task_change_due_id = wx.NewId()
		self.task_change_start_id = wx.NewId()
		self.task_change_remind_id = wx.NewId()
		self.task_change_hide_until_id = wx.NewId()
		self.task_change_context_id = wx.NewId()
		self.task_change_project_id = wx.NewId()
		self.task_change_folder_id = wx.NewId()
		self.task_change_status_id = wx.NewId()
		self.task_change_priority_id = wx.NewId()
		self.toggle_task_stared_id = wx.NewId()
		self.task_set_starred_id = wx.NewId()
		self.task_set_not_starred_id = wx.NewId()

	def build(self, task):
		""" Build popup menu for given (selected) task """
		menu = wx.Menu()
		menu.Append(self.toggle_task_complete_id, _('Set Task Not Completed')
				if task.completed else _('Set Task Completed'))
		menu.Append(self.toggle_task_stared_id, _('Set Task Not Starred')
				if task.starred else _('Set Task Starred'))
		menu.AppendSeparator()
		menu.Append(self.task_edit_id, _('Edit Task'))
		menu.Append(self.task_clone_id, _('Clone Task'))
		menu.Append(self.task_delete_id, _('Delete Task'))
		menu.AppendSeparator()
		menu.Append(self.task_change_project_id, _('Change Project/List...'))
		if task.type != enums.TYPE_CHECKLIST_ITEM:
			menu.Append(self.task_change_context_id, _('Change Context...'))
			menu.Append(self.task_change_folder_id, _('Change Folder...'))
			menu.Append(self.task_change_status_id, _('Change Status...'))
		menu.Append(self.task_change_priority_id, _('Change Priority...'))
		if task.type not in (enums.TYPE_CHECKLIST, enums.TYPE_CHECKLIST_ITEM):
			menu.AppendSeparator()
			menu.Append(self.task_change_due_id, _('Change Due Date...'))
			menu.Append(self.task_change_start_id, _('Change Start Date...'))
			menu.Append(self.task_change_remind_id, _('Change Remind Date...'))
			menu.Append(self.task_change_hide_until_id,
					_('Change Show Settings..'))
		return menu

	def build_multi(self, _types):
		""" Build popup menu for >1 selected tasks """
		menu = wx.Menu()
		menu.Append(self.task_set_complete_id, _('Set Task Completed'))
		menu.Append(self.task_set_not_complete_id, _('Set Task Not Completed'))
		menu.Append(self.task_set_starred_id, _('Set Task Starred'))
		menu.Append(self.task_set_not_starred_id, _('Set Task Not Starred'))
		menu.AppendSeparator()
		menu.Append(self.task_delete_id, _('Delete Task'))
		menu.AppendSeparator()
		menu.Append(self.task_change_project_id, _('Change Project/List...'))
		menu.Append(self.task_change_context_id, _('Change Context...'))
		menu.Append(self.task_change_folder_id, _('Change Folder...'))
		menu.Append(self.task_change_status_id, _('Change Status...'))
		menu.Append(self.task_change_priority_id, _('Change Priority...'))
		menu.AppendSeparator()
		menu.Append(self.task_change_due_id, _('Change Due Date...'))
		menu.Append(self.task_change_start_id, _('Change Start Date...'))
		menu.Append(self.task_change_remind_id, _('Change Remind Date...'))
		menu.Append(self.task_change_hide_until_id, _('Change Show Settings...'))
		return menu
