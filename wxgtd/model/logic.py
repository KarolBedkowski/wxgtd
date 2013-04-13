#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Operacje na obiekatch
"""

import uuid
import datetime
import logging

from dateutil.relativedelta import relativedelta

import objects as OBJ
import enums

_LOG = logging.getLogger(__name__)


def update_task_alarm(task):
	"""Aktualizacja Task.alarm na podstawie

	Formaty:
		- data i czas
		- due
		x minutes
		x hours
		x days
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
	if period.startswith('day'):
		offset = datetime.timedelta(days=-num)
	elif period.startswith('hour'):
		offset = datetime.timedelta(hours=-num)
	elif period.startswith('minute'):
		offset = datetime.timedelta(minutes=-num)
	else:
		_LOG.warn('update_task_alarm: invalid alarm_pattern = %r',
				alarm_pattern)
		return
	task.alarm = task.due_date + offset
	_LOG.debug('update_task_alarm result=%r', task.alarm)


def update_task_hide(task):
	""" Aktualizacja Task.hide_until na postawie Task.hide_pattern i
	pozostłaych pól"""
	hide_pattern = task.hide_pattern
	_LOG.debug('update_task_hide: date=%r, pattern=%r', task.hide_until,
			task.hide_pattern)
	if not hide_pattern:
		task.hide_until = None
		return
	elif hide_pattern == 'give date':
		return
	elif hide_pattern == "task is due":
		task.hide_until = task.due_date
		return
	num, period, dummy_, rel = hide_pattern.split(' ')
	rel_date = task.due_date if rel == 'due' else task.start_date
	if not rel_date:
		return
	num = float(num)
	if period == 'week':
		offset = datetime.timedelta(0, weeks=-num)
	elif period.startswith('day'):
		offset = datetime.timedelta(-num)
	elif period.startswith('month'):
		offset = relativedelta(months=-num)
	else:
		_LOG.warn('update_task_hide: invalid hide_period = %r',
			hide_pattern)
		return
	task.hide_until = rel_date + offset


_OFFSETS = {'Daily': relativedelta(days=1),
		'Weekly': relativedelta(weeks=+1),
		'Biweekly': relativedelta(weeks=+2),
		'Monthly': relativedelta(months=+1),
		'Bimonthly': relativedelta(months=+2),
		'Quarterly': relativedelta(months=+3),
		'Semiannually': relativedelta(months=+6),
		'Yearly': relativedelta(years=+1)}


def _move_date_repeat(date, repeat_pattern):
	if not repeat_pattern:
		return date
	if not date:
		return date
	offset = _OFFSETS.get(repeat_pattern)
	if offset is not None:
		return date + offset
	weekday = date.weekday()
	if repeat_pattern == 'Businessday':
		# pn - pt
		if weekday < 4:  # pn-cz
			return date + relativedelta(days=1)
		return date + relativedelta(days=(7 - weekday))
	if repeat_pattern == 'Weekend':
		if weekday == 5:  # so
			return date + relativedelta(days=1)
		if weekday == 6:
			return date + relativedelta(days=6)
		return date + relativedelta(days=(5 - weekday))
	return date


def _get_date(date, repeat_from_completed):
	if repeat_from_completed:
		today = datetime.datetime.today()
		date = today.replace(hour=date.hour, minute=date.minute,
				second=date.second)
	return date


def repeat_task(task):
	if not task.repeat_pattern:
		return None
	_LOG.info('repeat_task %r', task)
	""" Trzeba zaktualizować:
		- datę startu
		- due
		- alarm
	"""
	# TODO: repeat_end (??) sprawdzić czy to jest używane
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
		ntask.due_date = _move_date_repeat(_get_date(task.due_date, repeat_from),
				repeat_pattern)
		offset = ntask.due_date - task.due_date
		ntask.start_date += offset
	else:
		ntask.start_date = _move_date_repeat(
				_get_date(task.start_date, repeat_from), repeat_pattern)
	if task.alarm:
		if task.alarm_pattern:
			update_task_alarm(ntask)
		elif offset:
			ntask.alarm += offset
		else:
			ntask.alarm = _move_date_repeat(task.alarm, repeat_pattern)
	update_task_hide(ntask)
	ntask.completed = None
	return ntask


def update_task_from_parent(task, parent_uuid, session, appconfig):
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
