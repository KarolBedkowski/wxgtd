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
import datetime
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
from wxgtd.logic import task as task_logic
from wxgtd.gui import dlg_about
from wxgtd.gui import _fmt as fmt
from wxgtd.gui import _infobox as infobox
from wxgtd.gui import message_boxes as mbox
from wxgtd.gui import _tasklistctrl as TLC
from wxgtd.gui import quicktask
from wxgtd.gui._base_frame import BaseFrame
from wxgtd.gui._filtertreectrl import FilterTreeCtrl
from wxgtd.gui._taskbaricon import TaskBarIcon
from wxgtd.gui.dlg_task import DlgTask
from wxgtd.gui.dlg_checklistitem import DlgChecklistitem
from wxgtd.gui.dlg_preferences import DlgPreferences
from wxgtd.gui.dlg_sync_progress import DlgSyncProggress
from wxgtd.gui.dlg_tags import DlgTags
from wxgtd.gui.dlg_goals import DlgGoals
from wxgtd.gui.dlg_folders import DlgFolders
from wxgtd.gui.dlg_reminders import DlgReminders
from wxgtd.gui.frame_notebooks import FrameNotebook

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
		BaseFrame.__init__(self)
		self._setup()

	def _setup(self):
		self._session = OBJ.Session()
		self._items_path = []
		self._last_reminders_check = None
		self._filter_tree_ctrl.RefreshItems()
		self._tbicon = TaskBarIcon(self.wnd)  # pylint: disable=W0201
		wx.CallAfter(self._refresh_list)
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

	def _create_bindings(self, wnd):
		BaseFrame._create_bindings(self, wnd)

		self._create_menu_bind('menu_file_load', self._on_menu_file_load)
		self._create_menu_bind('menu_file_save', self._on_menu_file_save)
		self._create_menu_bind('menu_file_exit', self._on_menu_file_exit)
		self._create_menu_bind('menu_file_sync', self._on_menu_file_sync)
		self._create_menu_bind('menu_file_preferences',
				self._on_menu_file_preferences)
		self._create_menu_bind('menu_help_about', self._on_menu_help_about)
		self._create_menu_bind('menu_task_new', self._on_menu_task_new)
		self._create_menu_bind('menu_task_quick', self._on_menu_task_quick)
		self._create_menu_bind('menu_task_edit', self._on_menu_task_edit)
		self._create_menu_bind('menu_task_delete', self._on_menu_task_delete)
		self._create_menu_bind('menu_task_clone', self._on_menu_task_clone)
		self._create_menu_bind('menu_task_notebook', self._on_menu_task_notebook)
		self._create_menu_bind('menu_sett_tags', self._on_menu_sett_tags)
		self._create_menu_bind('menu_sett_goals', self._on_menu_sett_goals)
		self._create_menu_bind('menu_sett_folders', self._on_menu_sett_folders)

		wnd.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self._on_filter_tree_item_activated,
				self._filter_tree_ctrl)
		wnd.Bind(CT.EVT_TREE_ITEM_CHECKED, self._on_filter_tree_item_selected,
				self._filter_tree_ctrl)
		wnd.Bind(wx.EVT_RADIOBOX, self._on_rb_show_selection,
				self['rb_show_selection'])
		wnd.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self._on_items_list_activated,
				self._items_list_ctrl)
		wnd.Bind(TLC.EVT_DRAG_TASK, self._on_item_drag, self._items_list_ctrl)
		wnd.Bind(wx.EVT_BUTTON, self._on_btn_path_back, id=wx.ID_UP)
		wnd.Bind(wx.EVT_BUTTON, self._on_btn_edit_parent,
				self['btn_parent_edit'])
		wnd.Bind(wx.EVT_TIMER, self._on_timer)

		Publisher().subscribe(self._on_tasks_update, ('task', 'update'))
		Publisher().subscribe(self._on_tasks_update, ('task', 'delete'))

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
				size=(150, -1))
		self._searchbox.SetDescriptiveText(_('Search'))
		self._searchbox.ShowCancelButton(True)
		toolbar.AddControl(self._searchbox)
		self.wnd.Bind(wx.EVT_TEXT, self._on_search, self._searchbox)
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
		self.wnd.Bind(wx.EVT_TOOL, self._on_menu_task_notebook, id=tbi.GetId())

		toolbar.Realize()

	# events

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

	def _on_menu_file_preferences(self, _evt):
		if DlgPreferences(self.wnd).run(True):
			self._filter_tree_ctrl.RefreshItems()

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

	def _on_menu_task_notebook(self, _evt):  # pylint: disable=R0201
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
			task = session.query(  # pylint: disable=E1101
					OBJ.Task).filter_by(uuid=task_uuid).first()
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

	def _on_item_drag(self, evt):
		s_index = evt.start
		e_index = evt.stop
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
		task_uuid = self._items_list_ctrl.get_item_uuid(None)
		if task_uuid is None:  # not selected
			return
		task_logic.toggle_task_complete(task_uuid, self.wnd, self._session)

	def _on_btn_edit_parent(self, _evt):
		if not self._items_path:
			return
		task_uuid = self._items_path[-1].uuid
		if task_uuid:
			dlg = DlgTask.create(task_uuid, self.wnd, task_uuid)
			dlg.run()

	def _on_btn_reminders(self, _evt):
		if not DlgReminders.check(self.wnd, self._session):
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
			DlgReminders.check(self.wnd, self._session)

	def _refresh_list(self):
		wx.SetCursor(wx.HOURGLASS_CURSOR)
		params = self._get_params_for_list()
		_LOG.debug("FrameMain._refresh_list; params=%r", params)
		self._session.expire_all()  # pylint: disable=E1101
		tasks = OBJ.Task.select_by_filters(params, session=self._session)
		active_only = params['finished'] is not None and not params['finished']
		self._items_list_ctrl.fill(tasks, active_only=active_only)
		showed = self._items_list_ctrl.GetItemCount()
		self.wnd.SetStatusText(ngettext("%d item", "%d items", showed) % showed, 1)
		self._show_parent_info(active_only)
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
			Publisher().sendMessage('task.update')

	def _delete_selected_task(self):
		task_uuid = self._items_list_ctrl.get_item_uuid(None)
		if task_uuid:
			task_logic.delete_task(task_uuid, self.wnd)

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
		if group_id == 5 and not self._items_path:
			task_type = enums.TYPE_PROJECT
		elif group_id == 6 and not self._items_path:
			task_type = enums.TYPE_CHECKLIST
		dlg = DlgTask(self.wnd, None, parent_uuid, task_type)
		dlg.run()

	def _edit_selected_task(self):
		task_uuid = self._items_list_ctrl.get_item_uuid(None)
		if task_uuid:
			dlg = DlgTask.create(task_uuid, self.wnd, task_uuid)
			dlg.run()

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

	def _get_params_for_list(self):
		""" Build params for database query """
		group_id = self['rb_show_selection'].GetSelection()
		parent = self._items_path[-1].uuid if self._items_path else None
		_LOG.debug('_get_params_for_list: group_id=%r, parent=%r', group_id, parent)
		tmodel = self._filter_tree_ctrl.model
		params = {'starred': False, 'min_priority': None,
				'max_due_date': None, 'types': None,
				'contexts': list(tmodel.checked_items_by_parent("CONTEXTS")),
				'folders': list(tmodel.checked_items_by_parent("FOLDERS")),
				'goals': list(tmodel.checked_items_by_parent("GOALS")),
				'statuses': list(tmodel.checked_items_by_parent("STATUSES")),
				'tags': list(tmodel.checked_items_by_parent("TAGS")),
				'hide_until': self._btn_hide_until.GetValue(),
				'search_str': self._searchbox.GetValue(),
				'parent_uuid': parent}
		params['finished'] = None if self._btn_show_finished.GetValue() else False
		if not parent and not self._btn_show_subtasks.GetValue():
			# tylko nadrzędne
			params['parent_uuid'] = 0
		if group_id == 1 and not parent:  # hot
			# ignore hotlist settings when showing subtasks
			_get_hotlist_settings(params, self._appconfig)
		elif group_id == 2 and not parent:  # stared
			# ignore starred when showing subtasks
			params['starred'] = True
		elif group_id == 3:  # basket
			# no status, no context
			params['contexts'] = [None]
			params['statuses'] = [0]
			params['goals'] = [None]
			params['folders'] = [None]
			params['tags'] = [None]
			params['finished'] = False
			params['no_due_date'] = True
		elif group_id == 4:  # finished
			params['finished'] = True
		elif group_id == 5 and not parent:  # projects
			params['types'] = [enums.TYPE_PROJECT]
		elif group_id == 6:  # checklists
			if parent:
				params['types'] = [enums.TYPE_CHECKLIST, enums.TYPE_CHECKLIST_ITEM]
			else:
				params['types'] = [enums.TYPE_CHECKLIST]
		elif group_id == 7:  # future alarms
			params['active_alarm'] = True
			params['finished'] = (None if self._btn_show_finished.GetValue()
					else False)
		return params


def _get_hotlist_settings(params, conf):
	now = datetime.datetime.utcnow()
	params['filter_operator'] = 'or' if conf.get('hotlist', 'cond', True) \
			else 'and'
	params['max_due_date'] = now + datetime.timedelta(days=conf.get('hotlist',
			'due', 0))
	params['min_priority'] = conf.get('hotlist', 'priority', 3)
	params['starred'] = conf.get('hotlist', 'starred', False)
	params['next_action'] = conf.get('hotlist', 'next_action', False)
	params['started'] = conf.get('hotlist', 'started', False)


# additional strings to translate
def _fake_strings():
	_('All')
	_('Hot')
	_('Stared')
	_('Basket')
	_('Finished')
	_('Projects')
	_('Checklists')
