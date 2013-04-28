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
from wx.lib.agw import ultimatelistctrl as ULC
import wx.lib.mixins.listctrl as listmix

from wxgtd.model import enums
from wxgtd.gui import _fmt as fmt
from wxgtd.wxtools import iconprovider

_ = gettext.gettext
_LOG = logging.getLogger(__name__)


class _ListItemRenderer(object):
	""" Renderer for one / first row of TaskListControl.

	Args:
		parent: parent windows (TaskListControl)
		task: task to disiplay
		overdue: task or any child of it are overdue.

	+-----------+-----------------------+------+---------------+
	| completed | title                 | due  | star, type    |
	| priority  | status, goal, project |      | alarm, repeat |
	+-----------+-----------------------+------+---------------+
	"""
	_line_height = None
	_font_task = None
	_font_info = None
	_info_offset = None

	def __init__(self, _parent, task, overdue=False):
		self._task = task
		self._overdue = overdue
		if not self._font_task:
			self._font_task = wx.Font(10, wx.NORMAL, wx.NORMAL, wx.BOLD, False)
		if not self._font_info:
			self._font_info = wx.Font(8, wx.NORMAL, wx.NORMAL, wx.NORMAL, False)

	def DrawSubItem(self, dc, rect, _line, _highlighted, _enabled):
		canvas = wx.EmptyBitmap(rect.width, rect.height)
		mdc = wx.MemoryDC()
		mdc.SelectObject(canvas)

		task = self._task

#		if highlighted:
#			mdc.SetBackground(wx.Brush(wx.SystemSettings_GetColour(
#					wx.SYS_COLOUR_HIGHLIGHT)))
#			mdc.SetTextForeground(wx.WHITE)
#		else:
#			mdc.SetBackground(wx.Brush(wx.SystemSettings_GetColour(
#					wx.SYS_COLOUR_WINDOW)))
		mdc.Clear()

		mdc.SetTextForeground(wx.RED if self._overdue else wx.BLACK)
		mdc.SetFont(self._font_task)
		mdc.DrawText(task.title, 0, 5)
		mdc.SetFont(self._font_info)
		info = fmt.format_task_info(task)
		if info:
			mdc.DrawText(info, 0, self._info_offset)
		dc.Blit(rect.x + 3, rect.y, rect.width - 6, rect.height, mdc, 0, 0)

	def GetLineHeight(self):
		if self._line_height:
			return self._line_height
		dc = wx.MemoryDC()
		dc.SelectObject(wx.EmptyBitmap(1, 1))
		dc.SetFont(self._font_task)
		dummy, ytext1 = dc.GetTextExtent("Agw")
		dc.SetFont(self._font_info)
		self._info_offset = ytext1 + 10
		dummy, ytext2 = dc.GetTextExtent("Agw")
		dc.SelectObject(wx.NullBitmap)
		self._line_height = ytext1 + ytext2 + 10
		return self._line_height

	def GetSubItemWidth(self):
		return 400


class TaskListControl(ULC.UltimateListCtrl, listmix.ColumnSorterMixin):
	""" TaskList Control based on wxListCtrl. """

	def __init__(self, parent, wid=wx.ID_ANY, pos=wx.DefaultPosition,
				size=wx.DefaultSize, style=0, agwStyle=0):
		agwStyle = agwStyle | wx.LC_REPORT | wx.BORDER_SUNKEN | wx.LC_HRULES \
				| wx.LC_SINGLE_SEL | ULC.ULC_HAS_VARIABLE_ROW_HEIGHT
		ULC.UltimateListCtrl.__init__(self, parent, wid, pos, size, style,
				agwStyle)
		listmix.ColumnSorterMixin.__init__(self, 4)
		self._icons = icon_prov = iconprovider.IconProvider()
		icon_prov.load_icons(['task_done', 'prio-1', 'prio0', 'prio1', 'prio2',
				'prio3', 'sm_up', 'sm_down'])
		self.SetImageList(icon_prov.image_list, wx.IMAGE_LIST_SMALL)
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
		self.Freeze()
		current_sort_state = self.GetSortState()
		if current_sort_state[0] == -1:
			current_sort_state = (2, 1)
		self._items.clear()
		self.itemDataMap.clear()
		self.DeleteAllItems()
		icon_completed = self._icons.get_image_index('task_done')
		prio_icon = {-1: self._icons.get_image_index('prio-1'),
				0: self._icons.get_image_index('prio0'),
				1: self._icons.get_image_index('prio1'),
				2: self._icons.get_image_index('prio2'),
				3: self._icons.get_image_index('prio3')}
		now = datetime.datetime.now()
		for task in tasks:
			info, task_is_overdue = fmt.format_task_info_icons(task,
					active_only)
			if info is None and task_is_overdue is None:
				continue
			task_is_overdue = task_is_overdue or (task.due_date and
					task.due_date < now)
			task_is_overdue = task_is_overdue and not task.completed
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
			self.SetStringItem(index, 3, info)
			self.SetItemData(index, index)
			self._items[index] = (task.uuid, task.type)
			self.itemDataMap[index] = tuple(_get_sort_info_for_task(task))
			if task_is_overdue:
				self.SetItemTextColour(index, wx.RED)
		self.SortListItems(*current_sort_state)
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

	# used by the ColumnSorterMixin
	def GetListCtrl(self):
		return self

	# Used by the ColumnSorterMixin
	def GetSortImages(self):
		return (self._icon_sm_down, self._icon_sm_up)


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
