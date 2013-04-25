# -*- coding: utf-8 -*-

"""
Formatery
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2010-2013"
__version__ = "2010-11-25"

import time
import logging
import datetime

from wxgtd.model import enums

_LOG = logging.getLogger(__name__)


def format_timestamp(timestamp, show_time):
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
	info = []
	if task.status:
		info.append(enums.STATUSES[task.status])
	if task.context:
		info.append(task.context.title)
	if task.goal:
		info.append("◎" + task.goal.title)
	if task.folder:
		info.append("▫" + task.folder.title)
	if task.tags:
		info.append("☘" + ",".join(tasktag.tag.title for tasktag in
			task.tags))
	if info:
		info = '  '.join(info)
	return info or None


_TASK_TYPE_ICONS = {enums.TYPE_TASK: "",
		enums.TYPE_PROJECT: "⛁",
		enums.TYPE_CHECKLIST: "☑",
		enums.TYPE_CHECKLIST_ITEM: "☑",
		enums.TYPE_NOTE: "⍰",
		enums.TYPE_CALL: "☎",
		enums.TYPE_EMAIL: "✉",
		enums.TYPE_SMS: "✍",
		enums.TYPE_RETURN_CALL: "☏"}


def format_task_info_icons(task, active_only):
	info = ""
	if task.starred:
		info += "★ "
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
		info += '⌚ '
	if task.repeat_pattern:
		info += '↻'  # ⥁
	return info, task_is_overdue
