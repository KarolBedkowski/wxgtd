#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Obiekty

"""
__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2013"
__version__ = "2013-03-02"


import logging
import gettext
import uuid
import time

import sorm

_LOG = logging.getLogger(__name__)
_ = gettext.gettext

STATUSES = {0: _("No Status"),  # no status
		1: _("Next Action"),
		2: _("Active"),
		3: _("Planning"),
		4: _("Delegated"),
		5: _("Waiting"),
		6: _("Hold"),
		7: _("Postponed"),
		8: _("Someday"),
		9: _("Canceled"),
		10: _("Reference")}

TYPE_TASK = 0
TYPE_PROJECT = 1
TYPE_CHECKLIST = 2
TYPE_CHECKLIST_ITEM = 2

TYPES = {TYPE_TASK: _("Task"),
		TYPE_PROJECT: _("Project"),
		TYPE_CHECKLIST: _("Checklist"),
		TYPE_CHECKLIST_ITEM: _("Checklist Item"),
		4: _("Note"),
		5: _("Call"),
		6: _("Email"),
		7: _("SMS"),
		8: _("Return Call")}


class BaseModel(sorm.Model):
	""" Bazowy model - tworzenie kluczy, aktualizacja timestampów """

	def save(self):
		if not self.uuid:
			self.uuid = str(uuid.uuid4())
		self.modified = self.created = time.time()
		sorm.Model.save(self)

	def update(self):
		self.modified = time.time()
		sorm.Model.update(self)

	@classmethod
	def selecy_by_modified_is_less(cls, timestamp):
		return cls.select(where_stmt=("modified < %d" % timestamp))


class Task(BaseModel):
	"""Task

	TODO:
		- tagi
		- importance - nie używane (?)
	"""
	_table_name = "tasks"
	_fields = ["parent_uuid", "uuid", "created", "modified", "completed",
			"deleted", "ordinal", "title", "note", "type", "starred",
			"status", "priority", "importance", "start_date",
			"start_time_set", "due_date", "due_date_project",
			"due_time_set", "due_date_mod", "floating_event", "duration",
			"energy_required", "repeat_from", "repeat_pattern",
			"repeat_end", "hide_pattern", "hide_until",
			"prevent_auto_purge", "trash_bin", "metainf", "folder_uuid",
			"context_uuid", "goal_uuid"]
	_primary_keys = ['uuid']
	_default_sort_order = "title"

	def __init__(self, *args, **kwargs):
		BaseModel.__init__(self, *args, **kwargs)
		self.folder = None
		self.context = None
		self.goal = None

	@property
	def status_name(self):
		return STATUSES.get(self.status or 0, '?')

	def _get_task_completed(self):
		return bool(self.completed)

	def _set_task_completed(self, value):
		if value:
			self.completed = time.time()
		else:
			self.completed = None

	task_completed = property(_get_task_completed, _set_task_completed)

	@classmethod
	def get_stared(cls):
		return cls.select(stared=1)

	@classmethod
	def get_finished(cls):
		return cls.select(where_stmt="completed is not null")

	@classmethod
	def select_by_filters(cls, contexts, folders, goals, statuses, types,
			parent_uuid, starred, min_priority, max_start_date,
			max_due_date, finished, tags):
		# TODO: tags
		where_stmt = []
		params = []
		for column, ids in (('context_uuid', contexts),
						('folder_uuid', folders), ('goal_uuid', goals),
						('status', statuses)):
			if ids:
				wstmt, wparams = _create_params_list(column, ids)
				where_stmt.append(wstmt)
				if wparams:
					params.extend(wparams)
		if types:
			if len(types) == 1:
				where_stmt.append("type=%d" % types[0])
			else:
				where_stmt.append("types in (%s)" % ",".join(map(str, types)))
		if starred:
			where_stmt.append('starred=1')
		if min_priority is not None:
			where_stmt.append('priority >= %d' % min_priority)
		if max_start_date:
			where_stmt.append('start_date <= %d' % max_start_date)
		if max_due_date:
			where_stmt.append('due_date <= %d' % max_due_date)
		if finished is not None:
			if finished:
				where_stmt.append("(completed='' or completed is null)")
			else:
				where_stmt.append("(completed<>'' and completed is not null)")
		if parent_uuid is not None:
			where_stmt.append("parent_uuid='%s'" % parent_uuid)
		where = ' AND '.join(where_stmt)
		sql, query_params = cls._create_select_query(where_stmt=where)
		query_params.extend(params)
		with sorm.DbConnection().get_cursor() as cursor:
			cursor.execute(sql, query_params)
			for row in cursor:
				values = dict((key, cls._fields[key].from_database(val))
							for key, val in dict(row).iteritems())
				obj = cls(**values)
				if obj.context_uuid:
					obj.context = Context.get(uuid=obj.context_uuid)
				yield obj

	@classmethod
	def all_projects(cls):
		return cls.select(type=TYPE_PROJECT)


class Folder(BaseModel):
	"""folder"""
	_table_name = "folders"
	_fields = ["parent_uuid", "uuid", "created", "modified", "deleted",
			"ordinal", "title", "note", "color", "visible"]
	_primary_keys = ['uuid']
	_default_sort_order = "title"

	def save(self):
		if not self.uuid:
			self.uuid = str(uuid.uuid4())
		self.modified = self.created = time.time()
		BaseModel.save(self)

	def update(self):
		self.modified = time.time()
		BaseModel.update(self)


class Context(BaseModel):
	"""context"""
	_table_name = "contexts"
	_fields = ["parent_uuid", "uuid", "created", "modified", "deleted",
			"ordinal", "title", "note", "color", "visible"]
	_primary_keys = ['uuid']
	_default_sort_order = "title"


class Tasknote(BaseModel):
	"""tasknote"""
	_table_name = "tasknotes"
	_fields = ["task_uuid", "created", "modified", "uuid", "ordinal",
			"title", "color", "visible"]
	_primary_keys = ['uuid']
	_default_sort_order = "title"


class Alarm(BaseModel):
	"""alarm"""

	_table_name = "alarms"
	_fields = ["task_uuid", "created", "modified", "uuid", "alarm",
			"reminder", "active", "note"]
	_primary_keys = ['uuid']


class Goal(BaseModel):
	""" Goal """

	_table_name = "goals"
	_fields = ["parent_uuid", "uuid", "created", "modified", "deleted",
			"ordinal", "title", "note", "time_period", "archived", "color",
			"visible"]
	_primary_keys = ['uuid']
	_default_sort_order = "title"


def _create_params_list(column, values):
	if len(values) == 1 and values[0] is None:
		return '(' + column + ' is null)', None
	res = '(' + column
	if None in values:
		values = values[:]
		values.remove(None)
		res += ' is null or ' + column
	res += ' in ('
	res += ','.join("?" * len(values))
	res += '))'
	return res, values


class Conf(sorm.Model):
	_table_name = 'wxgtd'
	_fields = ['key', 'val']
	_primary_keys = ['key']
