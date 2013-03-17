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

import sorm

_LOG = logging.getLogger(__name__)
_ = gettext.gettext

STATUSES = {0: _("No Status"),  # no status
		1: _("Next Action"),
		2: _("Active"),
		3: _("Planned")}


class Task(sorm.Model):
	"""Task"""
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
	_default_sort_order = "ordinal, title"

	def __init__(self, *args, **kwargs):
		sorm.Model.__init__(self, *args, **kwargs)
		self.folder = None
		self.context = None
		self.goal = None

	@property
	def status_name(self):
		return STATUSES.get(self.status or 0, '?')

	@classmethod
	def get_stared(cls):
		return cls.select(stared=1)

	@classmethod
	def get_finished(cls):
		return cls.select(where_stmt="completed is not null")

	@classmethod
	def select_by_filters(cls, contexts, folders, goals, statuses):
		where_stmt = []
		params = []
		for column, ids in (('context_uuid', contexts),
				('folder_uuid', folders), ('goal_uuid', goals),
				('status', statuses)):
			if ids:
				wstmt, wparams = _create_params_list(column, ids)
				if wstmt:
					where_stmt.append(wstmt)
					if wparams:
						params.extend(wparams)
		where = ' and '.join(where_stmt)
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


class Folder(sorm.Model):
	"""folder"""
	_table_name = "folders"
	_fields = ["parent_uuid", "uuid", "created", "modified", "deleted",
			"ordinal", "title", "note", "color", "visible"]
	_primary_keys = ['uuid']
	_default_sort_order = "ordinal"


class Context(sorm.Model):
	"""context"""
	_table_name = "contexts"
	_fields = ["parent_uuid", "uuid", "created", "modified", "deleted",
			"ordinal", "title", "note", "color", "visible"]
	_primary_keys = ['uuid']
	_default_sort_order = "ordinal"


class Tasknote(sorm.Model):
	"""tasknote"""
	_table_name = "tasknotes"
	_fields = ["task_uuid", "created", "modified", "uuid", "ordinal",
			"title", "color", "visible"]
	_primary_keys = ['uuid']
	_default_sort_order = "ordinal"


class Alarm(sorm.Model):
	"""alarm"""

	_table_name = "alarms"
	_fields = ["task_uuid", "created", "modified", "uuid", "alarm",
			"reminder", "active", "note"]
	_primary_keys = ['uuid']


class Goal(sorm.Model):
	""" Goal """

	_table_name = "goals"
	_fields = ["parent_uuid", "uuid", "created", "modified", "deleted",
			"ordinal", "title", "note", "time_period", "archived", "color",
			"visible"]
	_primary_keys = ['uuid']


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
