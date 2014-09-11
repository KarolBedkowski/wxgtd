# -*- coding: utf-8 -*-
## pylint: disable-msg=W0401, C0103
"""Info box draw function.

Copyright (c) Karol Będkowski, 2013

This file is part of wxGTD
Licence: GPLv2+
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2013"
__version__ = "2013-05-20"

import gettext
import logging

import wx

from wxgtd.model import enums
from wxgtd.wxtools import iconprovider

_ = gettext.gettext
_LOG = logging.getLogger(__name__)


SETTINGS = {}


def configure():
	if SETTINGS:
		return SETTINGS
	SETTINGS['font_task'] = wx.Font(10, wx.NORMAL, wx.NORMAL, wx.BOLD, False)
	SETTINGS['font_info'] = wx.Font(8, wx.NORMAL, wx.NORMAL, wx.NORMAL, False)

	# info line height
	dc = wx.MemoryDC()
	dc.SelectObject(wx.EmptyBitmap(1, 1))
	dc.SetFont(SETTINGS['font_task'])
	dummy, ytext1 = dc.GetTextExtent("Agw")
	dc.SetFont(SETTINGS['font_info'])
	dummy, ytext2 = dc.GetTextExtent("Agw")
	dc.SelectObject(wx.NullBitmap)
	SETTINGS['line_height'] = ytext1 + ytext2 + 10


_TYPE_ICON_NAMES = {enums.TYPE_PROJECT: 'project_big',
		enums.TYPE_CHECKLIST: 'checklist_big',
		enums.TYPE_CHECKLIST_ITEM: 'checklistitem_big',
		enums.TYPE_CALL: 'call_big',
		enums.TYPE_EMAIL: 'mail_big',
		enums.TYPE_SMS: 'sms_big',
		enums.TYPE_RETURN_CALL: 'returncall_big'}


def draw_info(mdc, task, overdue, cache):
	""" Draw information about task on given DC.

	Args:
		mdc: DC canvas
		task: task to render
		overdue: is task overdue
	"""
	main_icon_y_offset = (SETTINGS['line_height'] - 32) / 2
	icon_name = _TYPE_ICON_NAMES.get(task.type)
	if icon_name:
		mdc.DrawBitmap(iconprovider.get_image(icon_name), 0, main_icon_y_offset,
				False)
	if task.completed:
		mdc.SetTextForeground(wx.Colour(150, 150, 150))
	elif overdue:
		mdc.SetTextForeground(wx.RED)
	else:
		mdc.SetTextForeground(wx.BLACK)
	mdc.SetFont(SETTINGS['font_task'])
	mdc.DrawText(task.title, 35, 5)
	mdc.SetFont(SETTINGS['font_info'])
	y_off = mdc.GetTextExtent("Agw")[1] + 10
	x_off = 35

	x_off = _draw_info_task_status(mdc, cache, task, x_off, y_off)
	x_off = _draw_info_task_context(mdc, cache, task, x_off, y_off)
	x_off = _draw_info_task_parent(mdc, cache, task, x_off, y_off)
	x_off = _draw_info_task_goal(mdc, cache, task, x_off, y_off)
	x_off = _draw_info_task_folder(mdc, cache, task, x_off, y_off)
	x_off = _draw_info_task_tags(mdc, cache, task, x_off, y_off)


def _draw_info_task_status(mdc, cache, task, x_off, y_off):
	task_status = cache.get('task_status')
	if task_status is None and task.status:
		cache['task_status'] = task_status = enums.STATUSES[task.status]
		cache['task_status_x_off'] = mdc.GetTextExtent(task_status)[0] + 10
	if task_status:
		mdc.DrawBitmap(iconprovider.get_image('status_small'), x_off,
				y_off, False)
		x_off += 15  # 12=icon
		mdc.DrawText(task_status, x_off, y_off)
		x_off += cache['task_status_x_off']
	return x_off


def _draw_info_task_context(mdc, cache, task, x_off, y_off):
	task_context = cache.get('task_context')
	if task_context is None and task.context:
		task_context = task.context.title
		if not task_context.startswith('@'):
			task_context = '@' + task_context
		cache['task_context'] = task_context
		cache['task_context_x_off'] = mdc.GetTextExtent(task_context)[0] + 10
	if task_context:
		mdc.DrawText(task_context, x_off, y_off)
		x_off += cache['task_context_x_off']
	return x_off


def _draw_info_task_parent(mdc, cache, task, x_off, y_off):
	task_parent = cache.get('task_parent')
	if task_parent is None and task.parent:
		task_parents = []
		while task.parent:
			task_parents.insert(0, task.parent.title)
			task = task.parent
		task_parent = '/'.join(task_parents)
		cache['task_parent'] = task_parent
		cache['task_parent_x_off'] = mdc.GetTextExtent(task_parent)[0] + 10
	if task_parent:
		mdc.DrawBitmap(iconprovider.get_image('project_small'), x_off,
				y_off, False)
		x_off += 15  # 12=icon
		mdc.DrawText(task_parent, x_off, y_off)
		x_off += cache['task_parent_x_off']
	return x_off


def _draw_info_task_goal(mdc, cache, task, x_off, y_off):
	task_goal = cache.get('task_goal')
	if task_goal is None and task.goal:
		cache['task_goal'] = task_goal = task.goal.title
		cache['task_goal_x_off'] = mdc.GetTextExtent(task_goal)[0] + 10
	if task_goal:
		mdc.DrawBitmap(iconprovider.get_image('goal_small'), x_off,
				y_off, False)
		x_off += 15  # 12=icon
		mdc.DrawText(task_goal, x_off, y_off)
		x_off += cache['task_goal_x_off']
	return x_off


def _draw_info_task_folder(mdc, cache, task, x_off, y_off):
	task_folder = cache.get('task_folder')
	if task_folder is None and task.folder:
		cache['task_folder'] = task_folder = task.folder.title
		cache['task_folder_x_off'] = mdc.GetTextExtent(task_folder)[0] + 10
	if task_folder:
		mdc.DrawBitmap(iconprovider.get_image('folder_small'), x_off,
				y_off, False)
		x_off += 15  # 12=icon
		mdc.DrawText(task_folder, x_off, y_off)
		x_off += cache['task_folder_x_off']
	return x_off


def _draw_info_task_tags(mdc, cache, task, x_off, y_off):
	task_tags = cache.get('task_tags')
	if task_tags is None and task.tags:
		cache['task_tags'] = task_tags = ",".join(
				tag.title for tag in task.tags)
	if task_tags:
		mdc.DrawBitmap(iconprovider.get_image('tag_small'), x_off,
				y_off, False)
		x_off += 15  # 12=icon
		mdc.DrawText(task_tags, x_off, y_off)
		#x_off += mdc.GetTextExtent(task_tags)[0] + 10
	return x_off


_TASK_TYPE_ICONS = {enums.TYPE_TASK: "",
		enums.TYPE_PROJECT: "project_small",
		enums.TYPE_CHECKLIST: "checklist_small",
		enums.TYPE_CHECKLIST_ITEM: "checklistitem_small",
		enums.TYPE_NOTE: "note_small",
		enums.TYPE_CALL: "call_small",
		enums.TYPE_EMAIL: "mail_small",
		enums.TYPE_SMS: "sms_small",
		enums.TYPE_RETURN_CALL: "returncall_small"}


def draw_icons(mdc, task, overdue, active_only, cache):
	""" Draw information icons about task on given DC.

	Args:
		mdc: DC canvas
		task: task to render
		overdue: is task overdue
		active_only: showing information only active subtask.
	"""
	mdc.SetFont(SETTINGS['font_info'])
	y_off = mdc.GetTextExtent("Agw")[1] + 10
	if task.starred:
		mdc.DrawBitmap(iconprovider.get_image('starred_small'), 0, 7, False)

	child_count = cache.get('child_count')
	if child_count is None:
		child_count = task.active_child_count if active_only else \
				task.child_count
		cache['child_count'] = child_count
	if child_count > 0:
		info = cache.get('info')
		if info is None:
			info = ''
			overdue = cache.get('overdue')
			if overdue > 0:
				info += "%d / " % overdue
			info += "%d" % child_count
			cache['info'] = info
		mdc.DrawText(info, 16, 7)
	if task.alarm:
		mdc.DrawBitmap(iconprovider.get_image('alarm_small'), 0, y_off,
				False)
	if task.repeat_pattern and task.repeat_pattern != 'Norepeat':
		mdc.DrawBitmap(iconprovider.get_image('repeat_small'), 16, y_off,
				False)
	if task.note:
		mdc.DrawBitmap(iconprovider.get_image('note_small'), 32, y_off,
				False)


class TaskInfoPanel(wx.Panel):
	""" Panel with information for given task. """

	def __init__(self, *args, **kwargs):
		wx.Panel.__init__(self, *args, **kwargs)
		self.task = None
		self.overdue = False
		self._values_cache = {}
		configure()
		self.Bind(wx.EVT_PAINT, self._on_paint)

	def set_task(self, task):
		self.task = task
		self._values_cache.clear()

	def _on_paint(self, _evt):
		dc = wx.BufferedPaintDC(self)
		bg = wx.Brush(wx.WHITE if self.task else self.GetBackgroundColour())
		dc.SetBackground(bg)
		dc.Clear()
		if self.task:
			draw_info(dc, self.task, self.overdue, self._values_cache)
		dc.EndDrawing()


class TaskIconsPanel(wx.Panel):
	""" Panel with status icons for given task. """

	def __init__(self, *args, **kwargs):
		wx.Panel.__init__(self, *args, **kwargs)
		self.task = None
		self.overdue = False
		self.active_only = False
		self._values_cache = {}
		configure()
		self.Bind(wx.EVT_PAINT, self._on_paint)

	def set_task(self, task):
		self.task = task
		self._values_cache.clear()

	def _on_paint(self, _evt):
		dc = wx.BufferedPaintDC(self)
		bg = wx.Brush(wx.WHITE if self.task else self.GetBackgroundColour())
		dc.SetBackground(bg)
		dc.Clear()
		if self.task:
			draw_icons(dc, self.task, self.overdue, self.active_only,
					self._values_cache)
		dc.EndDrawing()
