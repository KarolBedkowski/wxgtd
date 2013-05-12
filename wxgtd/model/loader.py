#!/usr/bin/python
# -*- coding: utf-8 -*-
""" Load data from GTD sync file format.

Copyright (c) Karol Będkowski, 2006-2013

This file is part of wxGTD
Licence: GPLv2+
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2013"
__version__ = '2013-04-21'

import os
import logging
import zipfile
import time
import datetime
import gettext
try:
	import cjson
	json_decoder = cjson.decode
	json_encoder = cjson.encode
except ImportError:
	import json
	json_decoder = json.loads
	json_encoder = json.dumps


from wxgtd.model import objects
from wxgtd.model import logic

_LOG = logging.getLogger(__name__)
_ = gettext.gettext


def _fake_update_func(*args, **kwargs):
	_LOG.info('progress %r %r', args, kwargs)


def load_from_file(filename, update_func=_fake_update_func):
	"""Load data from (zip)file.

	Args:
		filename: file to load
		update_func: function called in each step.

	Returns:
		True if success.
	"""
	if not os.path.isfile(filename):
		update_func(50, _("File not found..."))
		return True
	update_func(0, _("Openning file"))
	if filename.endswith('.zip'):
		with zipfile.ZipFile(filename, 'r') as zfile:
			fname = zfile.namelist()[0]
			return load_json(zfile.read(fname), update_func)
	else:
		with open(filename, 'r') as ifile:
			return load_json(ifile.read(), update_func)
	return False


def _create_or_update(session, cls, datadict):
	""" Create object given class or update existing with loaded data.

	Args:
		session: sqlalchemy session
		cls: class object to load/created.
		datadict: data (dict) to set in object

	Returns:
		Updated or created object.
	"""
	uuid = datadict.pop('uuid')
	obj = session.query(cls).filter_by(uuid=uuid).first()
	if obj:
		modified = datadict.get('modified')
		if not modified or modified > obj.modified:
			# load only modified objs
			obj.load_from_dict(datadict)
	else:
		obj = cls(uuid=uuid)
		obj.load_from_dict(datadict)
		session.add(obj)
	return obj


def _replace_ids(objdict, cache, key_id, key_uuid=None):
	""" Replace ids objects in loaded data by suitable uuid.

	Args:
		objdict: loaded data as dict
		cache: dict id -> uuid
		key_id: name of key attibute in objdict
		key_uuid: name of attibute that will be set to uuid. By default
			key_id[:-2] + "uuid".

	Returns:
		Founded uuid or None.
	"""
	key = objdict.get(key_id)
	res = None
	if key:
		uuid = cache.get(key)
		if uuid:
			key_uuid = key_uuid or (key_id[:-2] + 'uuid')
			objdict[key_uuid] = uuid
			res = uuid
		else:
			_LOG.warn('missing key in cache %r', repr((objdict, key_id,
					key_uuid, key)))
	elif key is None:
		_LOG.warn('missing key %r', repr((objdict, key_id, key_uuid, key)))
	return res


def str2timestamp(string):
	""" Convert string like '2013-03-22T21:27:46.461Z' into timestamp.

	Args:
		string: string to convert

	Returns:
		Timestamp as long or None if error.
	"""
	if string and len(string) > 18:
		try:
			return time.mktime(time.strptime(string[:19], "%Y-%m-%dT%H:%M:%S"))
		except ValueError:
			_LOG.exception("str2timestamp %r", string)
	return None


def _convert_timestamps(dictobj, *fields):
	""" Converts timestamps in string into datetime objects in read data.

	Converted are for default "created", "modified", "deleted".

	Args:
		dictobj: loaded object as dict
		fields: list of additional fields to convert
	"""
	def convert(field):
		value = dictobj.get(field)
		if value is None:
			return
		elif value:
			value = datetime.datetime.fromtimestamp(str2timestamp(value))
		dictobj[field] = value or None

	for field in ('created', 'modified', 'deleted'):
		convert(field)
	for field in fields:
		convert(field)


def _delete_missing(objcls, ids, last_sync):
	""" Delete old object given class.

	Deleted are objects given class, thats uuids not found in list ``ids``
	and with last date of modification < ``last_sync``.

	Args:
		objcls: object class for search / delete
		ids: list of uuid to keep
		last_sync: items with modification older that this date will be deleted.
	"""
	objs = objcls.selecy_by_modified_is_less(last_sync)
	to_delete = []
	for obj in objs:
		if obj.uuid not in ids:
			to_delete.append(obj)
	for obj in to_delete:
		_LOG.info("_delete_missing %r", obj)
		obj.delete()


def _build_id_uuid_map(objects_list):
	""" Build dict that map id to uuid.

	Args:
		objects_list: list of dict containing loaded objects.

	Returns:
		Dict[id->uuid] for all objects.
	"""
	cache = {}
	for obj in objects_list or []:
		uuid = obj.get('uuid')
		oid = obj.get('_id')
		if uuid and oid:
			cache[oid] = uuid
	return cache


def _check_synclog(data, session):
	""" Check synclog for last modification.
	"""
	last_sync = 0
	c_last_sync = session.query(objects.Conf).filter_by(key='last_sync').first()
	if c_last_sync is None:
		return True
	last_sync = str2timestamp(c_last_sync.val)
	device_id = session.query(objects.Conf).filter_by(key='deviceId').first().val

	synclog = data.get('syncLog')[0]
	file_sync_time_str = synclog.get('syncTime')
	file_sync_time = str2timestamp(file_sync_time_str)
	sync_device = synclog.get('deviceId')

	if last_sync >= file_sync_time and device_id == sync_device:
		_LOG.info("_check_synclog last_sync=%r, file=%r", c_last_sync.val,
				file_sync_time_str)
		#return False
	return True


def load_json(strdata, update_func):
	""" Load data from json string.

	Args:
		strdata: json-encoded data
		update_func: function called on each step.

	Returns:
		true if success.
	"""
	update_func(2, _("Decoding.."))
	data = json_decoder(strdata.decode('UTF-8'))
	session = objects.Session()

	update_func(5, _("Checking..."))
	if not _check_synclog(data, session):
		update_func(2, _("Don't load"))
		_LOG.info("load_json: no loading file")
		return True

	_LOG.info("load_json: folder")
	update_func(6, _("Loading folders"))
	folders = data.get('folder')
	folders_cache = _build_id_uuid_map(folders)
	for folder in sorted(folders or []):  # musi być sortowane,
		# bo nie znajdzie parenta
		_replace_ids(folder, folders_cache, 'parent_id')
		_convert_timestamps(folder)
		_create_or_update(session, objects.Folder, folder)
	if folders:
		del data['folder']
	update_func(10, _("Loaded %d folders") % len(folders_cache))

	_LOG.info("load_json: context")
	update_func(11, _("Loading contexts"))
	contexts = data.get('context')
	contexts_cache = _build_id_uuid_map(contexts)
	for context in sorted(contexts or []):
		_replace_ids(context, contexts_cache, 'parent_id')
		_convert_timestamps(context)
		_create_or_update(session, objects.Context, context)
	if contexts:
		del data['context']
	update_func(15, _("Loaded %d contexts") % len(contexts_cache))

	# Goals
	_LOG.info("load_json: goals")
	update_func(16, _("Loading goals"))
	goals = data.get('goal')
	goals_cache = _build_id_uuid_map(goals)
	for goal in sorted(goals or []):
		_replace_ids(goal, goals_cache, 'parent_id')
		_convert_timestamps(goal)
		_create_or_update(session, objects.Goal, goal)
	if goals:
		del data['goal']
	update_func(20, _("Loaded %d goals") % len(goals_cache))

	_LOG.info("load_json: tasks")
	update_func(21, _("Loading tasks"))
	tasks = data.get('task')
	tasks_cache = _build_id_uuid_map(tasks)
	for task in sorted(tasks or []):
		_replace_ids(task, tasks_cache, 'parent_id')
		_convert_timestamps(task, 'completed', 'start_date', 'due_date',
				'due_date_project', 'hide_until')
		task['context_uuid'] = None
		task['folder_uuid'] = None
		task['goal_uuid'] = None
		task_obj = _create_or_update(session, objects.Task, task)
		logic.update_task_hide(task_obj)
	if tasks:
		del data['task']
	update_func(38, _("Loaded %d tasks") % len(tasks_cache))

	_LOG.info("load_json: tasknote")
	update_func(39, _("Loading task notes"))
	tasknotes = data.get('tasknote')
	tasknotes_cache = _build_id_uuid_map(tasknotes)
	for tasknote in tasknotes or []:
		_replace_ids(tasknote, tasks_cache, 'task_id')
		_convert_timestamps(tasknote)
		_create_or_update(session, objects.Tasknote, tasknote)
	if tasknotes:
		del data['tasknote']
	update_func(43, _("Loaded %d task notes") % len(tasknotes_cache))

	_LOG.info("load_json: alarms")
	update_func(44, _("Loading alarms"))
	alarms = data.get('alarm')
	for alarm in alarms or []:
		task_uuid = _replace_ids(alarm, tasks_cache, 'task_id')
		if not task_uuid:
			_LOG.error('load alarm error %r; %r; %r', alarm, task_uuid)
			continue
		_convert_timestamps(alarm, 'alarm')
		task = session.query(objects.Task).filter_by(uuid=task_uuid).first()
		if task.modified <= alarm['modified']:
			task.alarm = alarm['alarm']
			logic.update_task_alarm(task)
		else:
			_LOG.debug('skip %r', alarm)
	update_func(46, _("Loaded %d alarms") % len(alarms))
	if alarms:
		del data['alarm']

	_LOG.info("load_json: task_folder")
	update_func(47, _("Loading task folders"))
	task_folders = data.get('task_folder')
	for task_folder in task_folders or []:
		task_uuid = _replace_ids(task_folder, tasks_cache, 'task_id')
		folder_uuid = _replace_ids(task_folder, folders_cache, 'folder_id')
		if not task_uuid or not folder_uuid:
			_LOG.error('load task folder error %r; %r; %r', task_folder,
					task_uuid, folder_uuid)
			continue
		_convert_timestamps(task_folder)
		task = session.query(objects.Task).filter_by(uuid=task_uuid).first()
		if task.modified <= task_folder['modified']:
			task.folder_uuid = folder_uuid
		else:
			_LOG.debug('skip %r', task_folder)
	update_func(51, _("Loaded %d task folders") % len(task_folders))
	if task_folders:
		del data['task_folder']

	_LOG.info("load_json: task_contexts")
	update_func(52, _("Loading task contexts"))
	task_contexts = data.get('task_context')
	for task_context in task_contexts or []:
		task_uuid = _replace_ids(task_context, tasks_cache, 'task_id')
		context_uuid = _replace_ids(task_context, contexts_cache, 'context_id')
		if not task_uuid or not context_uuid:
			_LOG.error('load task contexts error %r; %r; %r', task_context,
					task_uuid, context_uuid)
			continue
		_convert_timestamps(task_context)
		task = session.query(objects.Task).filter_by(uuid=task_uuid).first()
		if task.modified <= task_context['modified']:
			task.context_uuid = context_uuid
		else:
			_LOG.debug('skip %r', task_context)
	update_func(56, _("Loaded %d tasks contexts") % len(task_contexts))
	if task_contexts:
		del data['task_context']

	_LOG.info("load_json: task_goal")
	update_func(57, _("Loading task goals"))
	task_goals = data.get('task_goal')
	for task_goal in task_goals or []:
		task_uuid = _replace_ids(task_goal, tasks_cache, 'task_id')
		goal_uuid = _replace_ids(task_goal, goals_cache, 'goal_id')
		if not task_uuid or not goal_uuid:
			_LOG.error('load task goal error %r; %r; %r', task_goal,
					task_uuid, goal_uuid)
			continue
		_convert_timestamps(task_goal)
		task = session.query(objects.Task).filter_by(uuid=task_uuid).first()
		if task.modified <= task_goal['modified']:
			task.goal_uuid = goal_uuid
		else:
			_LOG.debug('skip %r', task_goal)
	update_func(61, _("Loaded %d task goals") % len(task_goals))
	if task_goals:
		del data['task_goal']

	# tagi
	_LOG.info("load_json: tag")
	update_func(62, _("Loading tags"))
	tags = data.get('tag')
	tags_cache = _build_id_uuid_map(tags)
	for tag in sorted(tags or []):
		_replace_ids(tag, tags_cache, 'parent_id')
		_convert_timestamps(tag)
		_create_or_update(session, objects.Tag, tag)
	if tags:
		del data['tag']
	update_func(66, _("Loaded %d tags") % len(tags))

	_LOG.info("load_json: task_tag")
	update_func(67, _("Loading task tags"))
	task_tags = data.get('task_tag')
	for task_tag in task_tags or []:
		task_uuid = _replace_ids(task_tag, tasks_cache, 'task_id')
		tag_uuid = _replace_ids(task_tag, tags_cache, 'tag_id')
		_convert_timestamps(task_tag)
		obj = session.query(objects.TaskTag).filter_by(task_uuid=task_uuid,
				tag_uuid=tag_uuid).first()
		if obj:
			modified = task_tag.get('modified')
			if not modified or not obj.modified or modified > obj.modified:
				obj.load_from_dict(task_tag)
		else:
			obj = objects.TaskTag(task_uuid=task_uuid, tag_uuid=tag_uuid)
			obj.load_from_dict(task_tag)
			session.add(obj)
	update_func(71, _("Loaded %d task tags") % len(task_tags))
	if task_tags:
		del data['task_tag']

	_LOG.info("load_json: czyszczenie")
	update_func(72, _("Cleanup"))
	# pokasowanie staroci
	synclog = data.get('syncLog')[0]
	file_sync_time = str2timestamp(synclog.get('syncTime'))
	_delete_missing(objects.Task, tasks_cache, file_sync_time)
	_delete_missing(objects.Folder, folders_cache, file_sync_time)
	_delete_missing(objects.Context, contexts_cache, file_sync_time)
	_delete_missing(objects.Tasknote, tasknotes_cache, file_sync_time)
	update_func(78, _("Cleanup done"))

	c_last_sync = session.query(objects.Conf).filter_by(key='last_sync').first()
	if c_last_sync is None:
		c_last_sync = objects.Conf(key='last_sync')
		session.add(c_last_sync)
	c_last_sync.val = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

	# load synclog
	_LOG.info("load_json: synclog")
	update_func(79, _("Loading synclog"))
	for sync_log in data.get('syncLog'):
		_convert_timestamps(sync_log, 'prevSyncTime', 'syncTime')
		slog_itm = objects.SyncLog.get(session, sync_time=sync_log['syncTime'],
				device_id=sync_log['deviceId'])
		if slog_itm:
			continue
		slog_item = objects.SyncLog()
		slog_item.device_id = sync_log['deviceId']
		slog_item.sync_time = sync_log['syncTime']
		slog_item.prev_sync_time = sync_log['prevSyncTime']
		session.add(slog_item)
	if sync_log:
		del data['syncLog']

	update_func(90, _("Commiting..."))
	session.commit()
	update_func(100, _("Load completed"))

	if data:
		_LOG.warn("Loader: remaining: %r", data.keys())
		_LOG.debug("Loader: remainig: %r", data)
	return True


def test():
	logging.basicConfig(level=logging.DEBUG,
			format='%(asctime)s %(levelname)-8s %(name)s - %(message)s')

	from wxgtd.model import db
	db.connect('wxgtd.db')
	print load_json(open('/home/k/GTD_SYNC.json').read(), _fake_update_func)

if __name__ == '__main__':
	test()
