# -*- coding: utf-8 -*-
## pylint: disable-msg=W0401, C0103
"""Info box draw function.

Copyright (c) Karol Będkowski, 2013

This file is part of wxGTD
Licence: GPLv2+
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2013"
__version__ = "2011-03-29"

import gettext
import logging

import wx

from wxgtd.model import enums
from wxgtd.wxtools import iconprovider

_ = gettext.gettext
_LOG = logging.getLogger(__name__)


def draw_info(mdc, task, overdue):
	font_task = wx.Font(10, wx.NORMAL, wx.NORMAL, wx.BOLD, False)
	font_info = wx.Font(8, wx.NORMAL, wx.NORMAL, wx.NORMAL, False)

	mdc.SetTextForeground(wx.RED if overdue else wx.BLACK)
	mdc.SetFont(font_task)
	mdc.DrawText(task.title, 0, 5)
	mdc.SetFont(font_info)
	inf_y_offset = mdc.GetTextExtent("Agw")[1] + 10
	inf_x_offset = 0
	if task.status:
		mdc.DrawBitmap(iconprovider.get_image('status_small'), inf_x_offset,
				inf_y_offset, False)
		inf_x_offset += 15  # 12=icon
		status_text = enums.STATUSES[task.status]
		mdc.DrawText(status_text, inf_x_offset, inf_y_offset)
		inf_x_offset += mdc.GetTextExtent(status_text)[0] + 10
	if task.context:
		context = task.context.title
		mdc.DrawText(context, inf_x_offset, inf_y_offset)
		inf_x_offset += mdc.GetTextExtent(context)[0] + 10
	if task.parent:
		mdc.DrawBitmap(iconprovider.get_image('project_small'), inf_x_offset,
				inf_y_offset, False)
		inf_x_offset += 15  # 12=icon
		parent = task.parent.title
		mdc.DrawText(parent, inf_x_offset, inf_y_offset)
		inf_x_offset += mdc.GetTextExtent(parent)[0] + 10
	if task.goal:
		mdc.DrawBitmap(iconprovider.get_image('goal_small'), inf_x_offset,
				inf_y_offset, False)
		inf_x_offset += 15  # 12=icon
		goal = task.goal.title
		mdc.DrawText(goal, inf_x_offset, inf_y_offset)
		inf_x_offset += mdc.GetTextExtent(goal)[0] + 10
	if task.folder:
		mdc.DrawBitmap(iconprovider.get_image('folder_small'), inf_x_offset,
				inf_y_offset, False)
		inf_x_offset += 15  # 12=icon
		folder = task.folder.title
		mdc.DrawText(folder, inf_x_offset, inf_y_offset)
		inf_x_offset += mdc.GetTextExtent(folder)[0] + 10
	if task.tags:
		mdc.DrawBitmap(iconprovider.get_image('tag_small'), inf_x_offset,
				inf_y_offset, False)
		inf_x_offset += 15  # 12=icon
		tags = ",".join(tasktag.tag.title for tasktag in task.tags)
		mdc.DrawText(tags, inf_x_offset, inf_y_offset)
		inf_x_offset += mdc.GetTextExtent(tags)[0] + 10


_TASK_TYPE_ICONS = {enums.TYPE_TASK: "",
		enums.TYPE_PROJECT: "project_small",
		enums.TYPE_CHECKLIST: "checklist_small",
		enums.TYPE_CHECKLIST_ITEM: "checklistitem_small",
		enums.TYPE_NOTE: "note_small",
		enums.TYPE_CALL: "call_small",
		enums.TYPE_EMAIL: "mail_small",
		enums.TYPE_SMS: "sms_small",
		enums.TYPE_RETURN_CALL: "returncall_small"}


def draw_icons(mdc, task, overdue, active_only):
	font = wx.Font(8, wx.NORMAL, wx.NORMAL, wx.NORMAL, False)
	mdc.SetFont(font)
	inf_y_offset = mdc.GetTextExtent("Agw")[1] + 10
	if task.starred:
		mdc.DrawBitmap(iconprovider.get_image('starred_small'), 0, 7, False)
		child_count = task.active_child_count if active_only else \
				task.child_count
	icon = _TASK_TYPE_ICONS.get(task.type)
	if icon:
		mdc.DrawBitmap(iconprovider.get_image(icon), 16, 7, False)
	child_count = task.active_child_count if active_only else \
			task.child_count
	if child_count > 0:
		info = ""
		overdue = task.child_overdue
		if overdue > 0:
			info += "%d / " % overdue
		info += "%d" % child_count
		mdc.DrawText(info, 32, 7)
	if task.alarm:
		mdc.DrawBitmap(iconprovider.get_image('alarm_small'), 0, inf_y_offset,
				False)
	if task.repeat_pattern and task.repeat_pattern != 'Norepeat':
		mdc.DrawBitmap(iconprovider.get_image('repeat_small'), 16, inf_y_offset,
				False)


class TaskInfoPanel(wx.Panel):
	def __init__(self, *args, **kwargs):
		wx.Panel.__init__(self, *args, **kwargs)
		self.task = None
		self.overdue = False
		self.Bind(wx.EVT_PAINT, self._on_paint)

	def _on_paint(self, _evt):
		dc = wx.BufferedPaintDC(self)
		self.PrepareDC(dc)
		bg = wx.Brush(self.GetBackgroundColour())
		dc.SetBackground(bg)
		dc.Clear()
		if self.task:
			draw_info(dc, self.task, self.overdue)
		dc.EndDrawing()


class TaskIconsPanel(wx.Panel):
	def __init__(self, *args, **kwargs):
		wx.Panel.__init__(self, *args, **kwargs)
		self.task = None
		self.overdue = False
		self.active_only = False
		self.Bind(wx.EVT_PAINT, self._on_paint)

	def _on_paint(self, _evt):
		dc = wx.BufferedPaintDC(self)
		self.PrepareDC(dc)
		bg = wx.Brush(self.GetBackgroundColour())
		dc.SetBackground(bg)
		dc.Clear()
		if self.task:
			draw_icons(dc, self.task, self.overdue, self.active_only)
		dc.EndDrawing()
