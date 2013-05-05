# -*- coding: utf-8 -*-
""" Various formatting function.

Copyright (c) Karol Będkowski, 2013

This file is part of wxGTD
Licence: GPLv2+
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2010-2013"
__version__ = "2013-04-27"

import sys
import time
import logging
import datetime

from wxgtd.model import enums

_LOG = logging.getLogger(__name__)

if sys.platform == 'win32':
	#  win32 don't support unicode fonts
	_TASK_TYPE_ICONS = {enums.TYPE_TASK: "",
			enums.TYPE_PROJECT: "P",
			enums.TYPE_CHECKLIST: "C",
			enums.TYPE_CHECKLIST_ITEM: "c",
			enums.TYPE_NOTE: "?",
			enums.TYPE_CALL: "C",
			enums.TYPE_EMAIL: "@",
			enums.TYPE_SMS: "S",
			enums.TYPE_RETURN_CALL: "R"}
	_REPEAT_CHAR = '×'
	_ALARM_CHAR = '! '
	_PARENT_CHAR = "^"
	_GOAL_CHAR = "*"
	_FOLDER_CHAR = "/"
	_TAG_CHAR = "#"
	_STARRED_CHAR = "* "
else:
	_TASK_TYPE_ICONS = {enums.TYPE_TASK: "",
			enums.TYPE_PROJECT: "⛁",
			enums.TYPE_CHECKLIST: "☑",
			enums.TYPE_CHECKLIST_ITEM: "☑",
			enums.TYPE_NOTE: "⍰",
			enums.TYPE_CALL: "☎",
			enums.TYPE_EMAIL: "✉",
			enums.TYPE_SMS: "✍",
			enums.TYPE_RETURN_CALL: "☏"}
	_REPEAT_CHAR = '↻'  # ⥁
	_ALARM_CHAR = '⌚ '
	_PARENT_CHAR = "⛁"
	_GOAL_CHAR = "◎"
	_FOLDER_CHAR = "▫"
	_TAG_CHAR = "☘"
	_STARRED_CHAR = "★ "


def format_timestamp(timestamp, show_time=True):
	""" Format date time object.

	Args:
		timestamp: date/time as str/unicode, datetime or number.
		show_time: if true also show time.
	"""
	if not timestamp:
		return ""
	if isinstance(timestamp, (str, unicode)):
		return timestamp
	if isinstance(timestamp, datetime.datetime):
		if show_time:
			return timestamp.strftime("%x %X")
		return timestamp.strftime("%x")
	if show_time:
		return time.strftime("%x %X", time.localtime(timestamp))
	return time.strftime("%x", time.localtime(timestamp))


def format_task_info(task):
	""" Format information about task (status, context, tags, etc.). """
	info = []
	if task.status:
		info.append(enums.STATUSES[task.status])
	if task.context:
		info.append(task.context.title)
	if task.parent:
		info.append(_PARENT_CHAR + task.parent.title)
	if task.goal:
		info.append(_GOAL_CHAR + task.goal.title)
	if task.folder:
		info.append(_FOLDER_CHAR + task.folder.title)
	if task.tags:
		info.append(_TAG_CHAR + ",".join(tasktag.tag.title for tasktag in
			task.tags))
	if info:
		info = '  '.join(info)
	return info or None


def format_task_info_icons(task, active_only):
	""" Format information about task (type, child count, repeat, alarm).

	Args:
		task: task to gather information
		active_only: count only active task/subtask.
	"""
	info = ""
	if task.starred:
		info += _STARRED_CHAR
	info += _TASK_TYPE_ICONS.get(task.type, "")
	task_is_overdue = False
	child_count = task.active_child_count if active_only else \
			task.child_count
	if active_only and child_count == 0 and task.completed:
		return None, None
	if child_count > 0:
		overdue = task.child_overdue
		if overdue > 0:
			info += " %d / " % overdue
			task_is_overdue = True
		info += " %d " % child_count
	info += '\n'
	if task.alarm:
		info += _ALARM_CHAR
	if task.repeat_pattern and task.repeat_pattern != 'Norepeat':
		info += _REPEAT_CHAR
	return info, task_is_overdue
