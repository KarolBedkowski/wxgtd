#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
"""

import os
import logging
import cjson
import zipfile
import datetime
import uuid
import gettext

import objects

_LOG = logging.getLogger(__name__)
_ = gettext.gettext


def _fake_update_func(*args, **kwargs):
	_LOG.info('progress %r %r', args, kwargs)


def save_to_file(filename, update_func=_fake_update_func, internal_fname=None):
	"""Load data from (zip)file.

	Load data from and insert/update it into database.

	Args:
		filename: source filename
		update_func: function that is called after each step
		internal_fname: name of file inside zip file; default - filename
			without ".zip" extension.
	"""
	if filename.endswith('.zip'):
		with zipfile.ZipFile(filename, 'w', zipfile.ZIP_DEFLATED) as zfile:
			fname = internal_fname or os.path.basename(filename[:-4])
			if not fname.endswith('.json'):
				fname += '.json'
			zfile.writestr(fname, save_json(update_func))
	else:
		with open(filename, 'w') as ifile:
			ifile.write(save_json(update_func))
	update_func(100, _("Saved"))


def fmt_date(value):
	if not value:
		return ""
	return value.strftime("%Y-%m-%dT%H:%M:%S.") + value.strftime("%f")[:3] + 'Z'


def _build_uuid_map(session, objclass):
	cache = {}
	for idx, obj in enumerate(session.query(objclass), 1):
		cache[obj.uuid] = idx
	return cache


def save_json(update_func):
	res = {'version': 2}

	session = objects.Session()

	# folders
	_LOG.info("save_json: folders")
	update_func(1, _("Saving folders"))
	folders_cache = _build_uuid_map(session, objects.Folder)
	folders = []
	for obj in session.query(objects.Folder):
		folder = {'_id': folders_cache[obj.uuid],
				'parent_id': folders_cache[obj.parent_uuid] if obj.parent_uuid
						else 0,
				'uuid': obj.uuid,
				'created': fmt_date(obj.created),
				'modified': fmt_date(obj.modified),
				'deleted': fmt_date(obj.deleted),
				'ordinal': obj.ordinal or 0,
				'title': obj.title or '',
				'note': obj.note or '',
				'bg_color': obj.bg_color or "FFFFFF00",
				'visible': obj.visible}
		folders.append(folder)
	if folders:
		res['folder'] = folders
	update_func(5, _("Saved %d folders") % len(folders))

	# contexts
	_LOG.info("save_json: contexts")
	update_func(6, _("Saving contexts"))
	contexts_cache = _build_uuid_map(session, objects.Context)
	contexts = []
	for obj in session.query(objects.Context):
		folder = {'_id': contexts_cache[obj.uuid],
				'parent_id': contexts_cache[obj.parent_uuid] if obj.parent_uuid
						else 0,
				'uuid': obj.uuid,
				'created': fmt_date(obj.created),
				'modified': fmt_date(obj.modified),
				'deleted': fmt_date(obj.deleted),
				'ordinal': obj.ordinal or 0,
				'title': obj.title or '',
				'note': obj.note or '',
				'bg_color': obj.bg_color or "FFFFFF00",
				'visible': obj.visible}
		contexts.append(folder)
	if contexts:
		res['context'] = contexts
	update_func(10, _("Saved %d contexts") % len(contexts))

	# goals
	_LOG.info("save_json: goals")
	update_func(11, _("Saving goals"))
	goals_cache = _build_uuid_map(session, objects.Goal)
	goals = []
	for obj in session.query(objects.Goal):
		folder = {'_id': goals_cache[obj.uuid],
				'parent_id': goals_cache[obj.parent_uuid] if obj.parent_uuid
						else 0,
				'uuid': obj.uuid,
				'created': fmt_date(obj.created),
				'modified': fmt_date(obj.modified),
				'deleted': fmt_date(obj.deleted),
				'ordinal': obj.ordinal or 0,
				'title': obj.title or '',
				'note': obj.note or '',
				'time_period': obj.time_period,
				'archived': obj.archived,
				'bg_color': obj.bg_color or "FFFFFF00",
				'visible': obj.visible}
		goals.append(folder)
	if goals:
		res['goal'] = goals
	update_func(15, _("Saved %d goals") % len(goals))

	update_func(16, _("Saving task, alarms..."))
	_LOG.info("save_json: tasks")
	tasks_cache = _build_uuid_map(session, objects.Task)
	tasks = []
	alarms = []
	task_folders = []
	task_contexts = []
	task_goals = []
	alarm_idx = 0
	for task in session.query(objects.Task):
		taskd = {'_id': tasks_cache[task.uuid],
				'parent_id': tasks_cache[task.parent_uuid] if task.parent_uuid
						else 0,
				'uuid': task.uuid,
				'created': fmt_date(task.created),
				'modified': fmt_date(task.modified),
				'completed': fmt_date(task.completed),
				'deleted': fmt_date(task.deleted),
				'ordinal': obj.ordinal or 0,
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
				"duration": task.duration or 0,  # TODO: nie data?
				"energy_required": task.energy_required,
				"repeat_from": task.repeat_from or 0,
				"repeat_pattern": task.repeat_pattern or "",
				"repeat_end": task.repeat_end or 0,
				"hide_pattern": task.hide_pattern or "",
				"hide_until": fmt_date(task.hide_until),
				"prevent_auto_purge": task.prevent_auto_purge or 0,
				"trash_bin": task.trash_bin or 0,
				"metainf": task.metainf or ''}
		tasks.append(taskd)
		if task.alarm:
			alarmd = {'_id': alarm_idx,
					'task_id': tasks_cache[task.uuid],
					'uuid': str(uuid.uuid4()),
					'created': fmt_date(task.created),
					'modified': fmt_date(task.modified),
					'alarm': fmt_date(task.alarm),
					'reminder': 0,
					'active': 1,
					'note': ""}
			alarms.append(alarmd)
			alarm_idx += 1
		if task.folder_uuid:
			tfolder = {'task_id': tasks_cache[task.uuid],
					'folder_id': folders_cache[task.folder_uuid],
					'created': fmt_date(task.created),
					'modified': fmt_date(task.modified)}
			task_folders.append(tfolder)
		if task.context_uuid:
			tcontext = {'task_id': tasks_cache[task.uuid],
					'context_id': contexts_cache[task.context_uuid],
					'created': fmt_date(task.created),
					'modified': fmt_date(task.modified)}
			task_contexts.append(tcontext)
		if task.goal_uuid:
			tgoal = {'task_id': tasks_cache[task.uuid],
					'goal_id': goals_cache[task.goal_uuid],
					'created': fmt_date(task.created),
					'modified': fmt_date(task.modified)}
			task_goals.append(tgoal)
	if tasks:
		res['task'] = tasks
		res['alarm'] = alarms
		res['task_folder'] = task_folders
		res['task_context'] = task_contexts
		res['task_goal'] = task_goals
	update_func(65, _("Saved %d tasks") % len(tasks))
	update_func(66, _("Saved %d alatms") % len(alarms))
	update_func(67, _("Saved %d task folders") % len(task_folders))
	update_func(68, _("Saved %d task contexts") % len(task_contexts))
	update_func(69, _("Saved %d task goals") % len(task_goals))

	update_func(70, _("Saving tags"))
	# tags
	_LOG.info("save_json: tags")
	tags_cache = _build_uuid_map(session, objects.Tag)
	tags = []
	for obj in session.query(objects.Tag):
		folder = {'_id': tags_cache[obj.uuid],
				'parent_id': tags_cache[obj.parent_uuid] if obj.parent_uuid
						else 0,
				'uuid': obj.uuid,
				'created': fmt_date(obj.created),
				'modified': fmt_date(obj.modified),
				'deleted': fmt_date(obj.deleted),
				'ordinal': obj.ordinal or 0,
				'title': obj.title or '',
				'note': obj.note or "",
				'bg_color': obj.bg_color or "FFFFFF00",
				'visible': obj.visible}
		tags.append(folder)
	if tags:
		res['tag'] = tags
	update_func(74, _("Saved %d tags") % len(tags))

	update_func(75, _("Saving task notes"))
	# tasknotes
	_LOG.info("save_json: tasknotes")
	tasknotes_cache = _build_uuid_map(session, objects.Tasknote)
	tasknotes = []
	for obj in session.query(objects.Tasknote):
		folder = {'_id': tasknotes_cache[obj.uuid],
				'task_id': tasks_cache[obj.task_uuid],
				'uuid': obj.uuid,
				'created': fmt_date(obj.created),
				'modified': fmt_date(obj.modified),
				'ordinal': obj.ordinal or 0,
				'title': obj.title or '',
				'bg_color': obj.bg_color or "FFEFFF00",
				'visible': obj.visible}
		tasknotes.append(folder)
	if tasknotes:
		res['tasknote'] = tasknotes
	update_func(79, _("Saved %d task notes") % len(tasknotes))

	update_func(80, _("Saving task tags"))
	tasktags = []
	for obj in session.query(objects.TaskTag):
		ttag = {'task_id': tasks_cache[obj.task_uuid],
				'tag_id': tags_cache[obj.tag_uuid],
				'created': fmt_date(obj.created),
				'modified': fmt_date(obj.modified)}
		tasktags.append(ttag)
	if tasktags:
		res['task_tag'] = tasktags
	update_func(84, _("Saved %d task tags") % len(tasktags))

	update_func(85, _("Sync log"))
	# synclog
	deviceId = session.query(objects.Conf).filter_by(key='deviceId').first()
	synclog = {
			'deviceId': deviceId.val,
			"prevSyncTime": "",
			"syncTime": fmt_date(datetime.datetime.now())}
	res['syncLog'] = [synclog]

	session.flush()
	update_func(80, _("Saving..."))

	return cjson.encode(res)


def _check_existing_synclock(lock_filename, my_device_id):
	""" Sprawdzenie, czy istniejący synclog jest nasz.
		return True = można synchronizować
				False = nie można
	"""
	if not os.path.isfile(lock_filename):
		return True
	data = None
	with open(lock_filename, 'r') as lock_file:
		data = cjson.decode(lock_file.read().decode('UTF-8'))
	if data:
		sync_device = data.get('deviceId')
		if sync_device != my_device_id:
			# lock utworzony przez inny program
			return False
	os.unlink(lock_filename)
	return True


def create_sync_lock(sync_filename):
	session = objects.Session()
	deviceId = session.query(objects.Conf).filter_by(key='deviceId').first()
	synclog = {
			'deviceId': deviceId.val,
			"startTime": fmt_date(datetime.datetime.now())}
	session.flush()

	lock_filename = os.path.join(os.path.dirname(sync_filename),
			'sync.locked')
	if not _check_existing_synclock(lock_filename, deviceId.val):
		return False
	with open(lock_filename, 'w') as ifile:
		ifile.write(cjson.encode(synclog))
	return True


def delete_sync_lock(sync_filename):
	lock_filename = os.path.join(os.path.dirname(sync_filename),
			'sync.locked')
	try:
		os.unlink(lock_filename)
	except:
		_LOG.exception('delete_sync_lock error %r', lock_filename)
