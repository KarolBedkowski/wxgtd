#!/usr/bin/python
# -*- coding: utf-8 -*-
""" Various function that operate on Task objects.

This file is part of wxGTD.
Copyright (c) Karol Będkowski, 2013
License: GPLv2+


"""
__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2013"
__version__ = "2013-04-19"

import uuid
import datetime
import logging
import gettext

from dateutil.relativedelta import relativedelta

from wxgtd.gui import message_boxes as mbox
from wxgtd.model import objects as OBJ
from wxgtd.model import enums

_LOG = logging.getLogger(__name__)
_ = gettext.gettext


def update_task_alarm(task):
	""" Update Task alarm field according to values other fields.

	Update Task.alarm according to value of field alarm_pattern and due_date.

	Args:
		task: Task for update

	Sample patterns:
		- no pattern - date and time in alarm
		- "due" - alarm=due_time
		- "x minute(s)", "x hour(s)", "x day(s)" before due date
	"""
	_LOG.debug('update_task_alarm: %r', task)
	alarm_pattern = task.alarm_pattern
	_LOG.debug('update_task_alarm: alarm=%r, pattern=%r', task.alarm,
			alarm_pattern)
	if not alarm_pattern:
		return
	if alarm_pattern == 'due':
		task.alarm = task.due_date
		return
	num, period = alarm_pattern.split(' ')
	num = float(num)
	if period in ('day', 'days'):
		offset = datetime.timedelta(days=-num)
	elif period in ('hour', 'hours'):
		offset = datetime.timedelta(hours=-num)
	elif period in ('minute', 'minutes'):
		offset = datetime.timedelta(minutes=-num)
	else:
		_LOG.warn('update_task_alarm: invalid alarm_pattern = %r',
				alarm_pattern)
		return
	task.alarm = task.due_date + offset
	_LOG.debug('update_task_alarm result=%r', task.alarm)


def update_task_hide(task):
	""" Update Task hide_until field.

	Update Task.hide_until according to values of field Task.hide_pattern and
	due_date, start_date

	Args:
		task: object Task

	Returns:
		True = task updated, no error

	Sample patterns:
		- "task is due"
		- "given date"
		- "<number> (weak|day|month) before (due|start)
	"""
	hide_pattern = task.hide_pattern
	_LOG.debug('update_task_hide: date=%r, pattern=%r, due=%r, start=%r',
			task.hide_until, task.hide_pattern, task.due_date, task.start_date)
	if not hide_pattern:
		task.hide_until = None
		return True
	elif hide_pattern == 'given date':
		if not task.hide_until:
			_LOG.warning("update_task_hide: given date + empty hide_until; %r",
					task)
		return True
	elif hide_pattern == "task is due":
		task.hide_until = task.due_date
		return True
	try:
		num, period, dummy_, rel = hide_pattern.split(' ')
		num = float(num)
	except ValueError:
		_LOG.warning("update_task_hide: wrong hide_pattern: %r",
				hide_pattern)
		return False
	rel_date = task.due_date if rel == 'due' else task.start_date
	if not rel_date:  # missing date
		return True
	if num < 1 or num > 99:
		_LOG.warning("update_task_hide: invalid hide_pattern (x): %r",
				hide_pattern)
		return False
	if period in ('week', 'weeks'):
		offset = datetime.timedelta(0, weeks=-num)
	elif period in ('day', 'days'):
		offset = datetime.timedelta(-num)
	elif period in ('month', 'months'):
		offset = relativedelta(months=-int(num))
	else:
		_LOG.warn('update_task_hide: invalid hide_period = %r',
			hide_pattern)
		return False
	task.hide_until = rel_date + offset
	return True


# Definition simple repeat patterns
_OFFSETS = {'Daily': relativedelta(days=1),
		'Weekly': relativedelta(weeks=+1),
		'Biweekly': relativedelta(weeks=+2),
		'Monthly': relativedelta(months=+1),
		'Bimonthly': relativedelta(months=+2),
		'Quarterly': relativedelta(months=+3),
		'Semiannually': relativedelta(months=+6),
		'Yearly': relativedelta(years=+1)}


def _move_date_repeat(date, repeat_pattern):
	""" Change date according to repeat_pattern.

	Args:
		date: date as datatime.datetime objects
		repeat_pattern: repeat definition

	Returns:
		Updated date
	"""
	# TODO: czy przy uwzględnianiu należy uwzględniać aktualną datę?
	if not repeat_pattern:
		return date
	if not date:
		return date
	offset = _OFFSETS.get(repeat_pattern)
	weekday = date.weekday()
	if offset is not None:
		date += offset
	elif repeat_pattern == 'Businessday':
		# pn - pt
		if weekday < 4:  # pn-cz
			return date + relativedelta(days=1)
		date += relativedelta(days=(7 - weekday))
	elif repeat_pattern == 'Weekend':
		if weekday == 5:  # so
			return date + relativedelta(days=1)
		if weekday == 6:
			return date + relativedelta(days=6)
		date += relativedelta(days=(5 - weekday))
	else:
		_LOG.warning("_move_date_repeat: unknown repeat_pattern: %r",
				repeat_pattern)
	return date


def _get_date(date, completed_date, repeat_from_completed):
	if repeat_from_completed:
		# copy time from start/due date
		date = completed_date.replace(hour=date.hour, minute=date.minute,
				second=date.second)
	return date


def repeat_task(task, reset_task=True):
	""" Create repeated task.

	If task has repeat_pattern create new task bassed on it and set new values
	for due_date, start_date and alarm.

	Args:
		task: Based task

	Returns:
		New task with updated values or None if no task is created
	"""
	# repeat_from : 1= from completed, 0= from start
	# TODO: repeat_end (??) sprawdzić czy to jest używane
	if not task.repeat_pattern or task.repeat_pattern == 'Norepeat':
		return None
	_LOG.info('repeat_task %r', task)
	ntask = task.clone()
	ntask.uuid = str(uuid.uuid4())
	repeat_pattern = task.repeat_pattern
	repeat_from = task.repeat_from
	if repeat_pattern == 'WITHPARENT':
		if not ntask.parent_uuid:
			_LOG.warn('repeat_task WITHPARENT parent_uuid == None: %r', task)
			return ntask
		repeat_pattern = ntask.parent.repeat_pattern
		repeat_from = ntask.parent.repeat_from
	offset = None
	if task.due_date:
		ntask.due_date = _move_date_repeat(_get_date(task.due_date,
				task.completed, repeat_from), repeat_pattern)
		offset = ntask.due_date - task.due_date
		ntask.start_date += offset
	else:
		ntask.start_date = _move_date_repeat(_get_date(task.start_date,
				task.completed, repeat_from), repeat_pattern)
	if task.alarm:
		if task.alarm_pattern:
			update_task_alarm(ntask)
		elif offset:
			ntask.alarm += offset
		else:
			ntask.alarm = _move_date_repeat(task.alarm, repeat_pattern)
	update_task_hide(ntask)
	ntask.completed = None
	# reset repeat pattern on previous task
	if reset_task:
		task.repeat_pattern = 'Norepeat'
	return ntask


def update_task_from_parent(task, parent_uuid, session, appconfig):
	""" Update (inherit) values from Task parent.

	Args:
		task: task for update
		parent_uuid: uuid source task (parent of task)
		session: sqlalchemy session
		appconfig: AppConfig instance - configuration what is inherited
	"""
	if not parent_uuid:
		return
	# znalezienie projektu w hierarchii; czy to ma sens?
	while parent_uuid:
		parent = session.query(OBJ.Task).filter_by(uuid=parent_uuid).first()
		if parent.type == enums.TYPE_PROJECT:
			break
		parent_uuid = parent.parent_uuid
	if not parent:
		_LOG.warn("update_task_from_parent: wrong parent %r", (task,
			parent_uuid))
		return
	if appconfig.get('tasks', 'inerit_context') and not task.context_uuid:
		task.context_uuid = parent.context_uuid
	if appconfig.get('tasks', 'inerit_goal') and not task.goal_uuid:
		task.goal_uuid = parent.goal_uuid
	if appconfig.get('tasks', 'inerit_folder') and not task.folder_uuid:
		task.folder_uuid = parent.folder_uuid
	if appconfig.get('tasks', 'inerit_tags') and not task.tags and parent.tags:
		for tasktag in parent.tags:
			task.task.append(OBJ.TaskTag(tag_uuid=tasktag.tag_uuid))


def delete_task(task_uuid, parent_wnd=None, session=None):
	""" Delete given task.

	Show confirmation and delete task from database.

	Args:
		task_uuid: task for delete
		parent_wnd: current wxWindow
		session: sqlalchemy session

	Returns:
		True = task deleted
	"""
	if not mbox.message_box_delete_confirm(parent_wnd, _("task")):
		return False

	session = session or OBJ.Session()
	task = session.query(OBJ.Task).filter_by(uuid=task_uuid).first()
	if not task:
		_LOG.warning("delete_task: missing task %r", task_uuid)
		return False

	session.delete(task)
	session.commit()
	return True
