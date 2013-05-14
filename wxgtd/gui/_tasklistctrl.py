# -*- coding: utf-8 -*-
## pylint: disable-msg=W0401, C0103
"""Task list control.

Copyright (c) Karol Będkowski, 2013

This file is part of wxGTD
Licence: GPLv2+
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2013"
__version__ = "2011-03-29"

import sys
import gettext
import logging
import datetime

import wx
import wx.lib.newevent
from wx.lib.agw import ultimatelistctrl as ULC
import wx.lib.mixins.listctrl as listmix

from wxgtd.model import enums
from wxgtd.gui import _fmt as fmt
from wxgtd.gui import _infobox as infobox
from wxgtd.wxtools import iconprovider

_ = gettext.gettext
_LOG = logging.getLogger(__name__)


BUTTON_SNOOZE = 1
BUTTON_DISMISS = 2

_ListBtnDismissEvent, EVT_LIST_BTN_DISMISS = wx.lib.newevent.NewEvent()
_ListBtnSnoozeEvent, EVT_LIST_BTN_SNOOZE = wx.lib.newevent.NewEvent()


class _ListItemRenderer(object):
	""" Renderer for secound col of TaskListControl.

	Args:
		parent: parent windows (TaskListControl)
		task: task to disiplay
		overdue: task or any child of it are overdue.

	+-----------+-----------------------+------+---------------+
	| completed | title                 | due  | star, type    |
	| priority  | status, goal, project |      | alarm, repeat |
	+-----------+-----------------------+------+---------------+
	"""

	def __init__(self, _parent, task, overdue=False):
		self._task = task
		self._overdue = overdue

	def DrawSubItem(self, dc, rect, _line, _highlighted, _enabled):
		canvas = wx.EmptyBitmap(rect.width, rect.height)
		mdc = wx.MemoryDC()
		mdc.SelectObject(canvas)
		mdc.Clear()
		infobox.draw_info(mdc, self._task, self._overdue)
		dc.Blit(rect.x + 3, rect.y, rect.width - 6, rect.height, mdc, 0, 0)

	def GetLineHeight(self):  # pylint: disable=R0201
		return infobox.SETTINGS['line_height']

	def GetSubItemWidth(self):  # pylint: disable=R0201
		return 400


class _ListItemRendererIcons(object):
	""" Renderer for one forth column.

	Args:
		parent: parent windows (TaskListControl)
		task: task to disiplay
		overdue: task or any child of it are overdue.

	+-----------+-----------------------+------+---------------+
	| completed | title                 | due  | star, type    |
	| priority  | status, goal, project |      | alarm, repeat |
	+-----------+-----------------------+------+---------------+
	"""
	_font_task = None
	_font_info = None

	def __init__(self, _parent, task, overdue=False, active_only=False):
		self._task = task
		self._overdue = overdue
		self._active_only = active_only
		if not self._font_task:
			self._font_task = wx.Font(10, wx.NORMAL, wx.NORMAL, wx.BOLD, False)
		if not self._font_info:
			self._font_info = wx.Font(8, wx.NORMAL, wx.NORMAL, wx.NORMAL, False)

	def DrawSubItem(self, dc, rect, _line, _highlighted, _enabled):
		canvas = wx.EmptyBitmap(rect.width, rect.height)
		mdc = wx.MemoryDC()
		mdc.SelectObject(canvas)
		mdc.Clear()
		infobox.draw_icons(mdc, self._task, self._overdue, self._active_only)
		dc.Blit(rect.x + 3, rect.y, rect.width - 6, rect.height, mdc, 0, 0)

	def GetLineHeight(self):  # pylint: disable=R0201
		return infobox.SETTINGS['line_height']

	def GetSubItemWidth(self):  # pylint: disable=R0201
		return 72


class TaskListControl(ULC.UltimateListCtrl, listmix.ColumnSorterMixin):
	""" TaskList Control based on wxListCtrl. """
	# pylint: disable=R0901

	def __init__(self, parent, wid=wx.ID_ANY,  # pylint: disable=R0913
			pos=wx.DefaultPosition, size=wx.DefaultSize, style=0, agwStyle=0,
			buttons=0):
		# configure infobox
		infobox.configure()
		agwStyle = agwStyle | wx.LC_REPORT | wx.BORDER_SUNKEN | wx.LC_HRULES \
				| wx.LC_SINGLE_SEL | ULC.ULC_HAS_VARIABLE_ROW_HEIGHT
		ULC.UltimateListCtrl.__init__(self, parent, wid, pos, size, style,
				agwStyle)
		listmix.ColumnSorterMixin.__init__(self, 4)
		self._icons = icon_prov = iconprovider.IconProvider()
		icon_prov.load_icons(['task_done', 'prio-1', 'prio0', 'prio1', 'prio2',
				'prio3', 'sm_up', 'sm_down'])
		self.SetImageList(icon_prov.image_list, wx.IMAGE_LIST_SMALL)
		self._buttons = buttons
		self._setup_columns()
		self._items = {}
		self.itemDataMap = {}  # for sorting
		self._icon_sm_up = icon_prov.get_image_index('sm_up')
		self._icon_sm_down = icon_prov.get_image_index('sm_down')

	@property
	def items(self):
		""" Get items showed in control.

		Returns:
			Dict idx -> (task.uuid, task.type)
		"""
		return self._items

	@property
	def selected(self):
		""" Get selected item index. """
		return self.GetNextItem(-1, wx.LIST_NEXT_ALL, wx.LIST_STATE_SELECTED)

	def get_item_uuid(self, idx):
		""" Get given or selected (when idx is None) task uuid. """
		if idx is None:
			idx = self.selected
			if idx < 0:
				return None, None
		return self._items[self.GetItemData(idx)][0]

	def fill(self, tasks, active_only=False):
		""" Fill the list with tasks.

		Args:
			task: list of tasks
			active_only: boolean - show/count only active tasks.
		"""
		# pylint: disable=R0915
		self.Freeze()
		current_sort_state = self.GetSortState()
		if current_sort_state[0] == -1:
			current_sort_state = (2, 1)
		self._items.clear()
		self.itemDataMap.clear()
		self._mainWin.HideWindows()  # workaround for some bug in ULC
		self.DeleteAllItems()
		icon_completed = self._icons.get_image_index('task_done')
		prio_icon = {-1: self._icons.get_image_index('prio-1'),
				0: self._icons.get_image_index('prio0'),
				1: self._icons.get_image_index('prio1'),
				2: self._icons.get_image_index('prio2'),
				3: self._icons.get_image_index('prio3')}
		now = datetime.datetime.utcnow()
		index = -1
		for task in tasks:
			child_count = task.active_child_count if active_only else \
					task.child_count
			if active_only and child_count == 0 and task.completed:
				continue
			task_is_overdue = ((task.due_date and task.due_date < now and
						not task.completed) or
						(child_count > 0 and task.child_overdue))
			icon = icon_completed if task.completed else prio_icon[task.priority]
			index = self.InsertImageStringItem(sys.maxint, "", icon)
			self.SetStringItem(index, 1, "")
			self.SetItemCustomRenderer(index, 1, _ListItemRenderer(self,
				task, task_is_overdue))
			if task.type == enums.TYPE_CHECKLIST_ITEM:
				self.SetStringItem(index, 2, str(task.importance + 1))
			else:
				self.SetStringItem(index, 2, fmt.format_timestamp(task.due_date,
						task.due_time_set).replace(' ', '\n'))
			self.SetItemCustomRenderer(index, 3, _ListItemRendererIcons(self,
				task, task_is_overdue, active_only))
			self.SetItemData(index, index)
			col = 4
			if self._buttons & BUTTON_DISMISS:
				item = self.GetItem(index, col)
				btn = wx.Button(self, -1, _("Dismiss"))
				btn.task = task.uuid
				item.SetWindow(btn)
				self.SetItem(item)
				col += 1
				self.Bind(wx.EVT_BUTTON, self._on_list_btn_dismiss_click,
						btn)
			if self._buttons & BUTTON_SNOOZE:
				item = self.GetItem(index, col)
				btn = wx.Button(self, -1, _("Snooze"))
				btn.task = task.uuid
				item.SetWindow(btn)
				self.SetItem(item)
				self.Bind(wx.EVT_BUTTON, self._on_list_btn_snooze_click,
						btn)
			self._items[index] = (task.uuid, task.type)
			self.itemDataMap[index] = tuple(_get_sort_info_for_task(task))
			if task_is_overdue:
				self.SetItemTextColour(index, wx.RED)
		self._mainWin.ResetCurrent()
		if index > 0:
			self.SortListItems(*current_sort_state)  # pylint: disable=W0142
		self.Thaw()
		self.Update()

	def _setup_columns(self):
		info = ULC.UltimateListItem()
		info._mask = wx.LIST_MASK_TEXT | wx.LIST_MASK_FORMAT
		info._format = 0
		info._text = _("Prio")
		self.InsertColumnInfo(0, info)

		info = ULC.UltimateListItem()
		info._format = wx.LIST_FORMAT_LEFT
		info._mask = wx.LIST_MASK_TEXT | wx.LIST_MASK_FORMAT
		info._image = []
		info._text = _("Title")
		self.InsertColumnInfo(1, info)

		info = ULC.UltimateListItem()
		info._format = wx.LIST_FORMAT_LEFT
		info._mask = wx.LIST_MASK_TEXT | wx.LIST_MASK_FORMAT
		info._image = []
		info._text = _("Due")
		self.InsertColumnInfo(2, info)

		info = ULC.UltimateListItem()
		info._format = wx.LIST_FORMAT_LEFT
		info._mask = wx.LIST_MASK_TEXT | wx.LIST_MASK_FORMAT
		info._image = []
		info._text = _("Info")
		self.InsertColumnInfo(3, info)

		self.SetColumnWidth(0, 24)
		self.SetColumnWidth(1, 500)
		self.SetColumnWidth(2, 100)
		self.SetColumnWidth(3, 70)

		col = 4
		if self._buttons & BUTTON_DISMISS:
			self.InsertColumnInfo(col, ULC.UltimateListItem())
			self.SetColumnWidth(col, 100)
			col += 1
		if self._buttons & BUTTON_SNOOZE:
			self.InsertColumnInfo(col, ULC.UltimateListItem())
			self.SetColumnWidth(col, 100)
			col += 1

	# used by the ColumnSorterMixin
	def GetListCtrl(self):
		return self

	# Used by the ColumnSorterMixin
	def GetSortImages(self):
		return (self._icon_sm_down, self._icon_sm_up)

	def _on_list_btn_dismiss_click(self, evt):
		wx.PostEvent(self, _ListBtnDismissEvent(
				task=evt.GetEventObject().task))

	def _on_list_btn_snooze_click(self, evt):
		wx.PostEvent(self, _ListBtnSnoozeEvent(
				task=evt.GetEventObject().task))


def _get_sort_info_for_task(task):
	""" Wartośći sortowań kolejnych kolumn dla danego zadania """
	due = tuple(task.due_date.timetuple()) if task.due_date else (9999, )
	# 1 col - priorytet
	yield (task.priority, task.importance, task.starred, due)
	# 2 col - nazwa
	yield task.title
	# 3 col - due / importance
	yield (task.importance or 0, due, 3 - task.starred, 10 - task.priority)
	# starred
	yield (task.starred, task.priority, task.importance, due)
