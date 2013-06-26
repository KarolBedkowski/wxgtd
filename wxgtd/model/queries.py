#!/usr/bin/python
# -*- coding: utf-8 -*-
""" Queries.

Copyright (c) Karol Będkowski, 2013

This file is part of wxGTD
Licence: GPLv2+
"""
__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2013"
__version__ = "2013-06-02"

import datetime

from wxgtd.lib.appconfig import AppConfig
from wxgtd.model import enums

# groups
QUERY_ALL_TASK = 0
QUERY_HOTLIST = 1
QUERY_STARRED = 2
QUERY_BASKET = 3
QUERY_FINISHED = 4
QUERY_PROJECTS = 5
QUERY_CHECKLISTS = 6
QUERY_FUTURE_ALARMS = 7
QUERY_TRASH = 8

# options
OPT_SHOW_FINISHED = 1
OPT_SHOW_SUBTASKS = 2
OPT_HIDE_UNTIL = 4


def build_query_params(query_group, options, parent, search_str):
	""" Build query params for selecting Tasks.

	Args:
		query_group: one of group from QUERY_*
		options: options from OPT_*
		parent: UUID parent task
		search_str: string to search in task title/note

	Returns:
		dict of params
	"""
	params = {'_query_group': query_group,
			'_options': options,
			'starred': False,
			'min_priority': None,
			'max_due_date': None,
			'types': None,
			'contexts': [],
			'folders': [],
			'goals': [],
			'statuses': [],
			'tags': [],
			'hide_until': options & OPT_HIDE_UNTIL == OPT_HIDE_UNTIL,
			'search_str': search_str,
			'parent_uuid': 0 if not parent and not options & OPT_SHOW_SUBTASKS
					else parent,
			'finished': None if options & OPT_SHOW_FINISHED == OPT_SHOW_FINISHED
					else False}
	if query_group == QUERY_HOTLIST:
		_get_hotlist_settings(params)
	elif query_group == QUERY_STARRED:
		if not parent:
			# ignore starred when showing subtasks
			params['starred'] = True
	elif query_group == QUERY_BASKET:
		# no status, no context
		params['contexts'] = [None]
		params['statuses'] = [0]
		params['goals'] = [None]
		params['folders'] = [None]
		params['tags'] = [None]
		params['finished'] = False
		params['no_due_date'] = True
	elif query_group == QUERY_FINISHED:
		params['finished'] = True
	elif query_group == QUERY_PROJECTS:
		if not parent:  # projects
			params['types'] = [enums.TYPE_PROJECT]
	elif query_group == QUERY_CHECKLISTS:  # checklists
		if parent:
			params['types'] = [enums.TYPE_CHECKLIST, enums.TYPE_CHECKLIST_ITEM]
		else:
			params['types'] = [enums.TYPE_CHECKLIST]
	elif query_group == QUERY_FUTURE_ALARMS:  # future alarms
		params['active_alarm'] = True
		params['finished'] = (None if options & OPT_SHOW_FINISHED ==
				OPT_SHOW_FINISHED else False)
	elif query_group == QUERY_TRASH:
		params['deleted'] = True
		params['hide_until'] = None
		params['parent_uuid'] = None
		params['finished'] = None
	return params


def query_params_append_contexts(params, contexts):
	if params['_query_group'] != QUERY_BASKET:
		params['contexts'].extend(contexts)
	return params


def query_params_append_folders(params, folders):
	if params['_query_group'] != QUERY_BASKET:
		params['folders'].extend(folders)
	return params


def query_params_append_goals(params, goals):
	if params['_query_group'] != QUERY_BASKET:
		params['goals'].extend(goals)
	return params


def query_params_append_statuses(params, statuses):
	if params['_query_group'] != QUERY_BASKET:
		params['statuses'].extend(statuses)
	return params


def query_params_append_tags(params, statuses):
	if params['_query_group'] != QUERY_BASKET:
		params['tags'].extend(statuses)
	return params


def _get_hotlist_settings(params):
	conf = AppConfig()
	now = datetime.datetime.utcnow()
	params['filter_operator'] = 'or' if conf.get('hotlist', 'cond', True) \
			else 'and'
	params['max_due_date'] = now + datetime.timedelta(days=conf.get('hotlist',
			'due', 0))
	params['min_priority'] = conf.get('hotlist', 'priority', 3)
	params['starred'] = conf.get('hotlist', 'starred', False)
	params['next_action'] = conf.get('hotlist', 'next_action', False)
	params['started'] = conf.get('hotlist', 'started', False)
