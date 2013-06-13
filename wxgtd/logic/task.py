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

import datetime
import logging
import gettext
import re

from dateutil.relativedelta import relativedelta

try:
	from wx.lib.pubsub.pub import Publisher
except ImportError:
	from wx.lib.pubsub import Publisher  # pylint: disable=E0611

from wxgtd.model import objects as OBJ
from wxgtd.model import enums

_LOG = logging.getLogger(__name__)
_ = gettext.gettext


def alarm_pattern_to_time(pattern):
	""" Find time offset according to given alarm|snooze pattern.

	Args:
		pattern: remind or snooze pattern (see: enums.SNOOZE_PATTERNS,
			enums.REMIND_PATTERNS)
	Return:
		Time offset as datetime.timedelta or None if wrong pattern.
	"""
	_LOG.debug('alarm_pattern_to_time: pattern=%r', pattern)
	num, period = pattern.split(' ')
	num = float(num)
	if period in ('day', 'days'):
		offset = datetime.timedelta(days=num)
	elif period in ('hour', 'hours'):
		offset = datetime.timedelta(hours=num)
	elif period in ('minute', 'minutes'):
		offset = datetime.timedelta(minutes=num)
	else:
		_LOG.warn('alarm_pattern: invalid pattern = %r', pattern)
		return None
	return offset


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
	if not alarm_pattern:
		return
	if alarm_pattern == 'due':
		task.alarm = task.due_date
		return
	offset = alarm_pattern_to_time(alarm_pattern)
	if offset:
		task.alarm = task.due_date - offset
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
	# pylint: disable=R0911
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
		task.hide_until = task.due_date or task.start_date
		return True
	try:
		num, period, dummy_, rel = hide_pattern.split(' ')
		num = float(num)
	except ValueError:
		_LOG.warning("update_task_hide: wrong hide_pattern: %r",
				hide_pattern)
		return False
	rel_date = ((task.due_date or task.start_date) if rel == 'due' else
			(task.start_date or task.due_date))
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
RE_REPEAT_XT = re.compile("^Every (\d+) (\w+)$", re.IGNORECASE)
RE_REPEAT_EVERYW = re.compile("^Every ((Mon|Tue|Wed|Thu|Fri|Sat|Sun),? ?)+$",
		re.IGNORECASE)
_WEEKDAYS = {'mon': 0,
		'tue': 1,
		'wed': 2,
		'thu': 3,
		'fri': 4,
		'sat': 5,
		'sun': 6}
_ORDINALS = {'first': 0,
		'second': 1,
		'third': 2,
		'fourth': 3,
		'fifth': 4}  # + last


def _move_date_repeat(date, repeat_pattern):
	""" Change date according to repeat_pattern.

	Args:
		date: date as datatime.datetime objects
		repeat_pattern: repeat definition

	Returns:
		Updated date
	"""
	# pylint: disable=R0911, R0912
	# TODO: czy przy uwzględnianiu należy uwzględniać aktualną datę?
	if not repeat_pattern:
		return date
	if not date:
		return date
	offset = _OFFSETS.get(repeat_pattern)
	weekday = date.weekday()
	if offset is not None:
		return date + offset
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
	elif repeat_pattern == 'Last day of every month':
		date = date + relativedelta(days=1) + relativedelta(months=1)
		return date.replace(day=1) + relativedelta(days=-1)
	elif repeat_pattern.startswith("Every "):
		m_repeat_xt = RE_REPEAT_XT.match(repeat_pattern.lower())
		# every X T
		if m_repeat_xt:
			num = int(m_repeat_xt.group(1))
			period = m_repeat_xt.group(2)
			if period in ("days", "day"):
				return date + relativedelta(days=+num)
			if period in ('weeks', 'week'):
				return date + relativedelta(weeks=+num)
			if period in ('months', 'month'):
				return date + relativedelta(months=+num)
			if period in ('years', 'year'):
				return date + relativedelta(years=+num)
		if RE_REPEAT_EVERYW.match(repeat_pattern):
			# every w
			days = [_WEEKDAYS[day.strip(" ,")]
					for day in repeat_pattern.lower().split(' ')[1:]]
			while True:
				date += relativedelta(days=+1)
				if date.weekday() in days:
					return date
	elif (repeat_pattern.startswith("The ")
			and repeat_pattern.endswith(' months')):
		# The X D every M months
		_foo, num_wday, wday, _foo, num_month, _foo = repeat_pattern.split(' ')
		num_month = int(num_month)
		wday = _WEEKDAYS[wday.lower()]
		date += relativedelta(months=+num_month)
		if num_wday == 'last':
			date += relativedelta(months=+1)
			date = date.replace(day=1) + relativedelta(days=-1)
			while date.weekday() != wday:
				date += relativedelta(days=-1)
			return date
		else:
			date = date.replace(day=1)
			cntr = _ORDINALS[num_wday]
			while True:
				if date.weekday() == wday:
					cntr -= 1
					if cntr < 0:
						return date
				date += relativedelta(days=1)
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
	ntask.uuid = OBJ.generate_uuid()
	ntask.update_modify_time()
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
		if ntask.start_date:
			ntask.start_date += offset
	elif ntask.start_date:
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
	parent = session.query(OBJ.Task).filter_by(uuid=parent_uuid).first()
	if not parent:
		_LOG.warn("update_task_from_parent: wrong parent %r", (task,
			parent_uuid))
		return
	if appconfig.get('task', 'inherit_context') and not task.context_uuid:
		task.context_uuid = parent.context_uuid
	if appconfig.get('task', 'inherit_goal') and not task.goal_uuid:
		task.goal_uuid = parent.goal_uuid
	if appconfig.get('task', 'inherit_folder') and not task.folder_uuid:
		task.folder_uuid = parent.folder_uuid
	if appconfig.get('task', 'inherit_tags') and not task.tags and parent.tags:
		for tasktag in parent.tags:
			task.task.append(OBJ.TaskTag(tag_uuid=tasktag.tag_uuid))


def delete_task(task, session=None):
	""" Delete given task.

	Show confirmation and delete task from database.

	Args:
		task: task for delete (Task or UUID)
		session: sqlalchemy session

	Returns:
		True = task deleted
	"""
	session = session or OBJ.Session()
	if isinstance(task, (str, unicode)):
		task = session.query(OBJ.Task).filter_by(uuid=task).first()
		if not task:
			_LOG.warning("delete_task: missing task %r", task)
			return False

	session.delete(task)
	session.commit()
	Publisher().sendMessage('task.delete', data={'task_uuid': task.uuid})
	return True


def complete_task(task, session=None):
	""" Complete task.

	Repeat task if necessary.

	Args:
		task: Task object
		session: sqlalchemy session

	Returns:
		True if task is completed
	"""
	# pylint: disable=E1101
	session = session or OBJ.Session.objects_session(task) or OBJ.Session()
	task.task_completed = True
	task.update_modify_time()
	if task.type == enums.TYPE_CHECKLIST_ITEM:
		# renumber task in chcecklist - move current task to the end
		task_importance = task.importance
		idx = task_importance - 1
		for idx, ntask in enumerate(session.query(OBJ.Task).
				filter(OBJ.Task.parent_uuid == task.parent_uuid,
					OBJ.Task.importance >= task_importance,
					OBJ.Task.uuid != task.uuid).
				order_by(OBJ.Task.importance), task_importance):
			ntask.importance = idx
		task.importance = idx + 1
	elif task.type == enums.TYPE_TASK:
		# repeat only regular task
		repeated_task = repeat_task(task)
		if repeated_task is not None:
			session.add(repeated_task)
	return True


def toggle_task_complete(task_uuid, session=None):
	""" Togle task complete flag.

	Args:
		task_uuid: UUID of task to change
		session: optional SqlAlchemy session
	Returns:
		True if ok
	"""
	session = session or OBJ.Session()
	task = session.query(  # pylint: disable=E1101
			OBJ.Task).filter_by(uuid=task_uuid).first()
	if not task.task_completed:
		if not complete_task(task, session):
			return False
	else:
		task.task_completed = False
	return save_modified_task(task, session)


_PERIOD_PL = {'Week': "Weeks", "Day": "Days", "Month": "Months",
		"Year": "Years"}


def build_repeat_pattern_every_xt(num, period):
	""" Build repeat pattern - Every <num> (Day|Month|Week|Year). """
	if num > 1:
		period = _PERIOD_PL[period]
	return "Every %d %s" % (num, period)


def build_repeat_pattern_every_w(mon, tue, wed, thu, fri, sat, sun):
	""" Build repeat pattern - Every <week day list>. """
	pattern = []
	if mon:
		pattern.append("Mon")
	if tue:
		pattern.append("Tue")
	if wed:
		pattern.append("Wed")
	if thu:
		pattern.append("Thu")
	if fri:
		pattern.append("Fri")
	if sat:
		pattern.append("Sat")
	if sun:
		pattern.append("Sun")
	return "Every " + ", ".join(pattern)


def build_repeat_pattern_every_xdm(num_weekday, weekday, num_months):
	""" Build repeat pattern - The <num> <weekday> every <num> month. """
	mname = "months" if num_months > 1 else "month"
	return "The %s %s every %d %s" % (num_weekday, weekday, num_months,
			mname)


def update_project_due_date(task):
	""" Update project due date.

	if `task` is project:
		1. copy due_date_project to due_date
		2. search for subtask with due_date < due_date_project
			- if found - set project.due_date to subtask.due_date
	if `task` is not project and have parent:
		1. if parent.due_date > task.due_date update parent due date

	Args:
		task: task to update
	"""
	if task.type == enums.TYPE_PROJECT:
		task.due_date = task.due_date_project
		for subtask in task.children:
			if subtask.due_date and subtask.due_date < task.due_date:
				task.due_date = subtask.due_date
				task.due_time_set = subtask.due_time_set
	elif task.due_date and task.parent and task.parent.type == enums.TYPE_PROJECT:
		if not task.parent.due_date or (task.due_date and task.parent.due_date >
				task.due_date):
			task.parent.due_date = task.due_date
			task.parent.due_time_set = task.due_time_set


def clone_task(task_uuid, session=None):
	""" Clone task.

	Args:
		task_uuid: task to clone
		session: optional SqlAlchemy session
	Returns:
		Cloned task UUID or None when error.
	"""
	session = session or OBJ.Session()
	task = session.query(OBJ.Task).filter_by(uuid=task_uuid).first()
	if not task:
		_LOG.warn("_clone_selected_task; missing task %r", task_uuid)
		return None
	new_task = task.clone()
	save_modified_task(new_task, session)
	Publisher().sendMessage('task.update', data={'task_uuid': new_task.uuid})
	return new_task.uuid


def save_modified_task(task, session=None):
	""" Save modified task.
	Update required fields.

	Args:
		task: task to save
		session: optional SqlAlchemy session
	Returns:
		True if ok.
	"""
	session = session or OBJ.Session()
	update_project_due_date(task)
	adjust_task_type(task, session)
	if task.type == enums.TYPE_CHECKLIST_ITEM:
		if not task.importance:
			task.importance = OBJ.Task.find_max_importance(task.parent_uuid,
					session) + 1
	task.update_modify_time()
	session.add(task)
	session.commit()  # pylint: disable=E1101
	Publisher().sendMessage('task.update', data={'task_uuid': task.uuid})
	return True


def adjust_task_type(task, session):
	""" Update task type when moving task to project/change type.
	Args:
		task: task to save
		session: SqlAlchemy session
	Returns:
		True if ok.
	"""
	if task.parent:
		# zadanie ma rodzica - ustalenie typu na podstawie parenta
		if task.parent.type == enums.TYPE_CHECKLIST:
			# na checkliście tylko elementy listy
			task.type = enums.TYPE_CHECKLIST_ITEM
		elif task.type == enums.TYPE_CHECKLIST_ITEM:
			# rodzic nie jest checklistą, więc gdy element należał do listy
			# zmiana na zwykłe zadanie
			task.type = enums.TYPE_TASK
	elif task.type == enums.TYPE_CHECKLIST_ITEM:
		# brak rodzica; elementy checlisty tylko w checklistach
		task.type = enums.TYPE_TASK
	if task.children:
		# aktualizacja potomków
		if task.type in (enums.TYPE_CHECKLIST, enums.TYPE_PROJECT):
			for subtask in task.children:
				adjust_task_type(subtask, session)
		else:
			# jeżeli to nie projakt ani checliksta to nie powinna mieć podzadań
			for subtask in task.children:
				# przesuniecie na poziom parenta
				subtask.parent = task.parent
				# poprawa typu
				adjust_task_type(subtask, session)
	return True


def change_task_parent(task, parent, session=None):
	""" Change task parent.

	Args:
		task: task to change (uuid or Task)
		parent: parent to set (uuid or Task)
		session: optional SqlAlchemy session
	Returns:
		True if parent was changed
	"""
	session = session or OBJ.Session()
	if isinstance(task, (str, unicode)):
		task = OBJ.Task.get(session, uuid=task)
	if parent is not None:
		if isinstance(parent, (str, unicode)):
			parent = OBJ.Task.get(session, uuid=parent)
	task.parent = parent
	return adjust_task_type(task, session)
