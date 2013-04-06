#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Operacje na obiekatch
"""

import datetime
import logging

from dateutil.relativedelta import relativedelta

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
	elif period.startwith('day'):
		offset = datetime.timedelta(-num)
	elif period.startwith('month'):
		offset = relativedelta(months=-num)
	else:
		_LOG.warn('update_task_hide: invalid hide_period = %r',
			hide_pattern)
		return
	task.hide_until = rel_date + offset
