#!/usr/bin/python
# -*- coding: utf-8 -*-
# pylint: disable=W0141
""" Function for duping content of database into file.

Copyright (c) Karol Będkowski, 2013

This file is part of wxGTD
Licence: GPLv2+
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2013"
__version__ = '2013-04-21'

import os
import logging
import zipfile
import datetime
import gettext
try:
	import cjson
	_JSON_DECODER = cjson.decode
	_JSON_ENCODER = cjson.encode
except ImportError:
	import json
	_JSON_DECODER = json.loads
	_JSON_ENCODER = json.dumps


from wxgtd.model import objects

_LOG = logging.getLogger(__name__)
_ = gettext.gettext


def _fake_update_func(*args, **kwargs):
	_LOG.info('progress %r %r', args, kwargs)


def save_to_file(filename, notify_cb=_fake_update_func, internal_fname=None):
	"""Load data from (zip)file.

	Load data from and insert/update it into database.

	Args:
		filename: source filename
		notify_cb: function that is called after each step
		internal_fname: name of file inside zip file; default - filename
			without ".zip" extension.
	"""
	if filename.endswith('.zip'):
		with zipfile.ZipFile(filename, 'w', zipfile.ZIP_DEFLATED) as zfile:
			fname = internal_fname or os.path.basename(filename[:-4])
			if not fname.endswith('.json'):
				fname += '.json'
			zfile.writestr(fname, dump_database_to_json(notify_cb))
	else:
		with open(filename, 'w') as ifile:
			ifile.write(dump_database_to_json(notify_cb))
	notify_cb(100, _("Saved"))


def fmt_date(date):
	""" Format date to format required by GTD.

	Args:
		date: date & time as datetime.datetime object

	Returns:
		formatted date or empty string when date is None
	"""
	if not date:
		return ""
	return date.strftime("%Y-%m-%dT%H:%M:%S.") + date.strftime("%f")[:3] + 'Z'


def _build_uuid_map(session, objclass):
	""" Create cache "object uuid" -> "object id" from object in database.

	Object id is generated from sequence for all object given class.

	Args:
		session: sqlalchemy session
		objclass: class of objects to query

	Returns:
		Dictionary uuid -> object id
	"""
	cache = {}
	for idx, obj in enumerate(session.query(objclass), 1):
		cache[obj.uuid] = idx
	return cache


_DEFAULT_BG_COLOR = "FFFFFF00"


def dump_database_to_json(notify_cb):
	""" Dump object in database to json string in GTD sync file format.

	Args:
		notify_cb: function called on each step.

	Returns:
		Data encoded in json format.
	"""
	res = {'version': 2}

	session = objects.Session()

	# pylint: disable=E1101
	c_last_sync = session.query(objects.Conf).filter_by(key='last_sync').first()
	# pylint: enable=E1101
	if c_last_sync is None:
		c_last_sync = objects.Conf(key='last_sync')
		session.add(c_last_sync)  # pylint: disable=E1101
	c_last_sync.val = fmt_date(datetime.datetime.utcnow())
	session.commit()  # pylint: disable=E1101

	# dump
	res['folder'], folders_cache = _dump_folders(session, notify_cb)
	res['context'], contexts_cache = _dump_contexts(session, notify_cb)
	res['goal'], goals_cache = _dump_goals(session, notify_cb)
	res_tasks, tasks_cache = _dump_tasks(session, notify_cb, folders_cache,
			contexts_cache, goals_cache)
	res.update(res_tasks)
	res['tag'], tags_cache = _dump_tags(session, notify_cb)
	res['tasknote'] = _dump_task_notes(session, notify_cb, tasks_cache)
	res['task_tag'] = _dump_task_tags(session, notify_cb, tasks_cache,
			tags_cache)
	res.update(_dump_notebooks(session, notify_cb, folders_cache))
	res['syncLog'] = _dump_synclog(session, notify_cb)

	session.commit()  # pylint: disable=E1101
	notify_cb(80, _("Saving..."))

	return _JSON_ENCODER(res)


def _check_existing_synclock(lock_filename, my_device_id):
	""" Check if lockfile exists.

	Args:
		lock_filename: full file path,
		my_device_id: device UUID

	Returns:
		False if sync is locked by other device.
	"""
	if not os.path.isfile(lock_filename):
		return True
	data = None
	with open(lock_filename, 'r') as lock_file:
		data = _JSON_DECODER(lock_file.read().decode('UTF-8'))
	if data:
		sync_device = data.get('deviceId')
		if sync_device != my_device_id:
			_LOG.debug("_check_existing_synclock; different devid %r, %r",
					sync_device, my_device_id)
			# lock utworzony przez inny program
			return False
	os.unlink(lock_filename)
	return True


def create_sync_lock(sync_filename):
	""" Check if lockfile exists in sync folder. Create if not.

	Args:
		sync_filename: path of sync file

	Returns:
		False, if directory is locked.
	"""
	session = objects.Session()
	device_id = session.query(objects.Conf).filter_by(  # pylint: disable=E1101
			key='deviceId').first()
	synclog = {'deviceId': device_id.val,
			"startTime": fmt_date(datetime.datetime.utcnow())}
	session.flush()  # pylint: disable=E1101

	lock_filename = os.path.join(os.path.dirname(sync_filename),
			'sync.locked')
	if not _check_existing_synclock(lock_filename, device_id.val):
		return False
	_LOG.debug('create_sync_lock: writing synclog: %r', lock_filename)
	with open(lock_filename, 'w') as ifile:
		ifile.write(_JSON_ENCODER(synclog))
	return True


def delete_sync_lock(sync_filename):
	""" Delete sync lock file.

	Args:
		sync_filename: path of sync file
	"""
	_LOG.debug('delete_sync_lock: %r', sync_filename)
	lock_filename = os.path.join(os.path.dirname(sync_filename),
			'sync.locked')
	try:
		os.unlink(lock_filename)
	except IOError:
		_LOG.exception('delete_sync_lock error %r', lock_filename)


def _dump_folders(session, notify_cb):
	_LOG.info("dump_database_to_json: folders")
	notify_cb(1, _("Saving folders"))
	folders_cache = _build_uuid_map(session, objects.Folder)
	folders = []
	for obj in session.query(objects.Folder):  # pylint: disable=E1101
		folder = {'_id': folders_cache[obj.uuid],
				'parent_id': folders_cache[obj.parent_uuid] if obj.parent_uuid
						else 0,
				'uuid': obj.uuid,
				'created': fmt_date(obj.created),
				'modified': fmt_date(obj.modified or obj.created),
				'deleted': fmt_date(obj.deleted),
				'ordinal': obj.ordinal or 0,
				'title': obj.title or '',
				'note': obj.note or '',
				'bg_color': obj.bg_color or _DEFAULT_BG_COLOR,
				'visible': obj.visible}
		folders.append(folder)
	notify_cb(5, _("Saved %d folders") % len(folders))
	return folders, folders_cache


def _dump_contexts(session, notify_cb):
	_LOG.info("dump_database_to_json: contexts")
	notify_cb(6, _("Saving contexts"))
	contexts_cache = _build_uuid_map(session, objects.Context)
	contexts = []
	for obj in session.query(objects.Context):  # pylint: disable=E1101
		folder = {'_id': contexts_cache[obj.uuid],
				'parent_id': contexts_cache[obj.parent_uuid] if obj.parent_uuid
						else 0,
				'uuid': obj.uuid,
				'created': fmt_date(obj.created),
				'modified': fmt_date(obj.modified or obj.created),
				'deleted': fmt_date(obj.deleted),
				'ordinal': obj.ordinal or 0,
				'title': obj.title or '',
				'note': obj.note or '',
				'bg_color': obj.bg_color or _DEFAULT_BG_COLOR,
				'visible': obj.visible}
		contexts.append(folder)
	notify_cb(10, _("Saved %d contexts") % len(contexts))
	return contexts, contexts_cache


def _dump_goals(session, notify_cb):
	_LOG.info("dump_database_to_json: goals")
	notify_cb(11, _("Saving goals"))
	goals_cache = _build_uuid_map(session, objects.Goal)
	goals = []
	for obj in session.query(objects.Goal):  # pylint: disable=E1101
		folder = {'_id': goals_cache[obj.uuid],
				'parent_id': goals_cache[obj.parent_uuid] if obj.parent_uuid
						else 0,
				'uuid': obj.uuid,
				'created': fmt_date(obj.created),
				'modified': fmt_date(obj.modified or obj.created),
				'deleted': fmt_date(obj.deleted),
				'ordinal': obj.ordinal or 0,
				'title': obj.title or '',
				'note': obj.note or '',
				'time_period': obj.time_period,
				'archived': obj.archived,
				'bg_color': obj.bg_color or _DEFAULT_BG_COLOR,
				'visible': obj.visible}
		goals.append(folder)
	notify_cb(15, _("Saved %d goals") % len(goals))
	return goals, goals_cache


def _dump_tasks(session, notify_cb, folders_cache, contexts_cache,
		goals_cache):
	notify_cb(16, _("Saving task, alarms..."))
	_LOG.info("dump_database_to_json: tasks")
	tasks_cache = _build_uuid_map(session, objects.Task)
	tasks = []
	alarms = []
	task_folders = []
	task_contexts = []
	task_goals = []
	for task in session.query(objects.Task):  # pylint: disable=E1101
		tasks.append({'_id': tasks_cache[task.uuid],
				'parent_id': tasks_cache[task.parent_uuid] if task.parent_uuid
						else 0,
				'uuid': task.uuid,
				'created': fmt_date(task.created),
				'modified': fmt_date(task.modified or task.created),
				'completed': fmt_date(task.completed),
				'deleted': fmt_date(task.deleted),
				'ordinal': task.ordinal or 0,
				'title': task.title or '',
				'note': task.note or "",
				'type': task.type or 0,
				'starred': 1 if task.starred else 0,
				'status': task.status or 0,
				'priority': task.priority,
				'importance': task.importance,
				'start_date': fmt_date(task.start_date),
				'start_time_set': task.start_time_set,
				'due_date': fmt_date(task.due_date),
				"due_date_project": fmt_date(task.due_date_project),
				"due_time_set": task.due_time_set or 0,
				"due_date_mod": task.due_date_mod or 0,
				"floating_event": task.floating_event,
				"duration": task.duration or 0,
				"energy_required": task.energy_required,
				"repeat_from": task.repeat_from or 0,
				"repeat_pattern": task.repeat_pattern or "",
				"repeat_end": task.repeat_end or 0,
				"hide_pattern": task.hide_pattern or "",
				"hide_until": fmt_date(task.hide_until),
				"prevent_auto_purge": task.prevent_auto_purge or 0,
				"trash_bin": task.trash_bin or 0,
				"metainf": task.metainf or ''})
		if task.alarm:
			alarms.append({'_id': len(alarms),
					'task_id': tasks_cache[task.uuid],
					'uuid': objects.generate_uuid(),
					'created': fmt_date(task.created),
					'modified': fmt_date(task.modified or task.created),
					'alarm': fmt_date(task.alarm),
					'reminder': 0,
					'active': 1,
					'note': ""})
		if task.folder_uuid:
			task_folders.append({'task_id': tasks_cache[task.uuid],
					'folder_id': folders_cache[task.folder_uuid],
					'created': fmt_date(task.created),
					'modified': fmt_date(task.modified or task.created)})
		if task.context_uuid:
			task_contexts.append({'task_id': tasks_cache[task.uuid],
					'context_id': contexts_cache[task.context_uuid],
					'created': fmt_date(task.created),
					'modified': fmt_date(task.modified or task.created)})
		if task.goal_uuid:
			task_goals.append({'task_id': tasks_cache[task.uuid],
					'goal_id': goals_cache[task.goal_uuid],
					'created': fmt_date(task.created),
					'modified': fmt_date(task.modified or task.created)})
	res = {'task': tasks,
			'alarm': alarms,
			'task_folder': task_folders,
			'task_context': task_contexts,
			'task_goal': task_goals}
	notify_cb(49, _("Saved %d tasks") % len(tasks))
	notify_cb(51, _("Saved %d alarms") % len(alarms))
	notify_cb(52, _("Saved %d task folders") % len(task_folders))
	notify_cb(53, _("Saved %d task contexts") % len(task_contexts))
	notify_cb(54, _("Saved %d task goals") % len(task_goals))
	return res, tasks_cache


def _dump_tags(session, notify_cb):
	notify_cb(55, _("Saving tags"))
	# tags
	_LOG.info("dump_database_to_json: tags")
	tags_cache = _build_uuid_map(session, objects.Tag)
	tags = []
	for obj in session.query(objects.Tag):  # pylint: disable=E1101
		folder = {'_id': tags_cache[obj.uuid],
				'parent_id': tags_cache[obj.parent_uuid] if obj.parent_uuid
						else 0,
				'uuid': obj.uuid,
				'created': fmt_date(obj.created),
				'modified': fmt_date(obj.modified or obj.created),
				'deleted': fmt_date(obj.deleted),
				'ordinal': obj.ordinal or 0,
				'title': obj.title or '',
				'note': obj.note or "",
				'bg_color': obj.bg_color or _DEFAULT_BG_COLOR,
				'visible': obj.visible}
		tags.append(folder)
	notify_cb(59, _("Saved %d tags") % len(tags))
	return tags, tags_cache


def _dump_task_notes(session, notify_cb, tasks_cache):
	notify_cb(60, _("Saving task notes"))
	# tasknotes
	_LOG.info("dump_database_to_json: tasknotes")
	tasknotes_cache = _build_uuid_map(session, objects.Tasknote)
	tasknotes = []
	for obj in session.query(objects.Tasknote):  # pylint: disable=E1101
		folder = {'_id': tasknotes_cache[obj.uuid],
				'task_id': tasks_cache[obj.task_uuid],
				'uuid': obj.uuid,
				'created': fmt_date(obj.created),
				'modified': fmt_date(obj.modified or obj.created),
				'ordinal': obj.ordinal or 0,
				'title': obj.title or '',
				'bg_color': obj.bg_color or "FFEFFF00",
				'visible': obj.visible}
		tasknotes.append(folder)
	notify_cb(64, _("Saved %d task notes") % len(tasknotes))
	return tasknotes


def _dump_task_tags(session, notify_cb, tasks_cache, tags_cache):
	notify_cb(65, _("Saving task tags"))
	tasktags = []
	for obj in session.query(objects.TaskTag):  # pylint: disable=E1101
		ttag = {'task_id': tasks_cache[obj.task_uuid],
				'tag_id': tags_cache[obj.tag_uuid],
				'created': fmt_date(obj.created),
				'modified': fmt_date(obj.modified or obj.created)}
		tasktags.append(ttag)
	notify_cb(69, _("Saved %d task tags") % len(tasktags))
	return tasktags


def _dump_synclog(session, notify_cb):
	notify_cb(78, _("Sync log"))
	# synclog
	sync_logs = []
	device_id = session.query(objects.Conf).filter_by(
			key='deviceId').first().val
	slog_item = objects.SyncLog.get(session, device_id=device_id)
	if slog_item:
		slog_item.prev_sync_time = slog_item.sync_time
	else:
		slog_item = objects.SyncLog()
		slog_item.device_id = device_id
	slog_item.sync_time = datetime.datetime.utcnow()
	session.add(slog_item)  # pylint: disable=E1101

	for sync_log in session.query(  # pylint: disable=E1101
			objects.SyncLog).order_by(objects.SyncLog.sync_time):
		sync_logs.append({
			'deviceId': sync_log.device_id,
			"prevSyncTime": fmt_date(sync_log.prev_sync_time),
			"syncTime": fmt_date(sync_log.sync_time)})
	return sync_logs


def _dump_notebooks(session, notify_cb, folders_cache):
	notify_cb(70, _("Saving notebooks..."))
	_LOG.info("dump_database_to_json: notebooks")
	notebooks_cache = _build_uuid_map(session, objects.NotebookPage)
	notebooks = []
	notebook_folders = []
	for notebook in session.query(objects.NotebookPage):  # pylint: disable=E1101
		notebooks.append({'_id': notebooks_cache[notebook.uuid],
				'uuid': notebook.uuid,
				'created': fmt_date(notebook.created),
				'modified': fmt_date(notebook.modified or notebook.created),
				'deleted': fmt_date(notebook.deleted),
				'ordinal': notebook.ordinal or 0,
				'title': notebook.title or '',
				'note': notebook.note or "",
				'starred': 1 if notebook.starred else 0,
				'bg_color': notebook.bg_color or "FFEFFF00",
				'visible': notebook.visible})
		if notebook.folder_uuid:
			notebook_folders.append({
					'notebook_id': notebooks_cache[notebook.uuid],
					'folder_id': folders_cache[notebook.folder_uuid],
					'created': fmt_date(notebook.created),
					'modified': fmt_date(notebook.modified or notebook.created)})
	res = {'notebook': notebooks,
			'notebook_folder': notebook_folders}
	notify_cb(76, _("Saved %d notebooks") % len(notebooks))
	notify_cb(77, _("Saved %d notebook folders") % len(notebook_folders))
	return res
