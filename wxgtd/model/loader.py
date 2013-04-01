#!/usr/bin/python
# -*- coding: utf-8 -*-
"""


TODO:
	- goals
"""

import logging
import cjson
import zipfile
import time

import objects

_LOG = logging.getLogger()


def load_from_file(filename):
	"""Load data from zipfile"""
	if filename.endswith('.zip'):
		with zipfile.ZipFile(filename, 'r') as zfile:
			load_json(zfile.read())
	else:
		with open(filename, 'r') as ifile:
			load_json(ifile.read())


def _create_or_update(cls, datadict, cache=None):
	oid = datadict.pop('_id')
	uuid = datadict.pop('uuid')
	obj = cls.get(uuid=uuid)
	if obj:
		modified = datadict.get('modified')
		if not modified or modified > obj.modified:
			# load only modified objs
			obj.load_from_dict(datadict)
			obj.update()
	else:
		obj = cls(uuid=uuid)
		obj.load_from_dict(datadict)
		obj.save()
	if cache is not None:
		cache[oid] = uuid
		cache[uuid] = oid


def _replace_ids(objdict, cache, key_id, key_uuid=None):
	key = objdict.get(key_id)
	if key:
		uuid = cache.get(key)
		if uuid:
			key_uuid = key_uuid or (key_id[:-2] + 'uuid')
			objdict[key_uuid] = uuid
		else:
			_LOG.warn('missing key in cache %r', repr((objdict, key_id,
					key_uuid)))
	else:
		_LOG.warn('missing key %r', repr((objdict, key_id, key_uuid)))


def str2timestamp(string):
	""" Convert timestamps like '2013-03-22T21:27:46.461Z'"""
	if string and len(string) > 18:
		try:
			return time.mktime(time.strptime(string[:19], "%Y-%m-%dT%H:%M:%S"))
		except:
			_LOG.exception("str2timestamp %r", string)


def _convert_timestamps(dictobj, *fields):
	def convert(field):
		value = dictobj.get(field)
		value = str2timestamp(value)
		dictobj[field] = value

	for field in ('created', 'modified', 'deleted'):
		convert(field)
	for field in fields:
		convert(field)


def _delete_missing(objcls, ids, last_sync):
	""" skasowanie starych obiektów klasy objcls, których uuid-y nie są w ids,
		o ile data modyfikacji < last_sync """
	objs = objcls.selecy_by_modified_is_less(last_sync)
	to_delete = []
	for obj in objs:
		if obj.uuid not in ids:
			to_delete.append(obj)
	for obj in to_delete:
		_LOG.info("_delete_missing %r", obj)
		obj.delete()


def load_json(strdata):
	data = cjson.decode(strdata)

	last_sync = 0
	c_last_sync = objects.Conf.get(key='last_sync')
	if c_last_sync:
		last_sync = c_last_sync.val
	else:
		c_last_sync = objects.Conf(key='last_sync')

	file_sync_time_str = data.get('syncLog')[0].get('syncTime')
	file_sync_time = str2timestamp(file_sync_time_str)

	if last_sync > file_sync_time:
		_LOG.info("no loading file time=%r, last sync=%r", last_sync,
				file_sync_time_str)

	folders_cache = {}
	folders = data.get('folder')
	for folder in folders or []:
		_replace_ids(folder, folders_cache, 'parent_id')
		_convert_timestamps(folder)
		_create_or_update(objects.Folder, folder, folders_cache)
	if folders:
		del data['folder']

	contexts_cache = {}
	contexts = data.get('context')
	for context in contexts or []:
		_replace_ids(context, contexts_cache, 'parent_id')
		_convert_timestamps(context)
		_create_or_update(objects.Context, context, contexts_cache)
	if contexts:
		del data['context']

	# Goals
	goals = data.get('goal')
	goals_cache = {}
	for goal in goals or []:
		_replace_ids(goal, goals_cache, 'parent_id')
		_create_or_update(objects.Goal, goal, goals_cache)
	if goal:
		del data['goal']

	tasks_cache = {}
	tasks = data.get('task')
	for task in tasks or []:
		_replace_ids(task, tasks_cache, 'parent_id')
		_convert_timestamps(task, 'completed', 'start_date', 'due_date',
				'due_date_project', 'hide_until')
		task['context_uuid'] = None
		task['folder_uuid'] = None
		task['goal_uuid'] = None
		_create_or_update(objects.Task, task, tasks_cache)
	if tasks:
		del data['task']

	tasknotes_cache = {}
	tasknotes = data.get('tasknote')
	for tasknote in tasknotes or []:
		_replace_ids(tasknote, tasks_cache, 'task_id')
		_convert_timestamps(tasknote)
		_create_or_update(objects.Tasknote, tasknote, tasknotes_cache)
	if tasknotes:
		del data['tasknote']

	alarms_cache = {}
	alarms = data.get('alarm')
	for alarm in alarms or []:
		_replace_ids(alarm, tasks_cache, 'task_id')
		_convert_timestamps(alarm, 'alarm')
		_create_or_update(objects.Alarm, alarm, alarms_cache)
	if alarms:
		del data['alarm']

	task_folders = data.get('task_folder')
	for task_folder in task_folders or []:
		_replace_ids(task_folder, tasks_cache, 'task_id')
		_replace_ids(task_folder, folders_cache, 'folder_id')
		_convert_timestamps(task_folder)
		task_uuid = task_folder['task_uuid']
		folder_uuid = task_folder['folder_uuid']
		task = objects.Task.get(uuid=task_uuid)
		task.folder_uuid = folder_uuid
		task.update()
	if task_folders:
		del data['task_folder']

	task_contexts = data.get('task_context')
	for task_context in task_contexts or []:
		_replace_ids(task_context, tasks_cache, 'task_id')
		_replace_ids(task_context, contexts_cache, 'context_id')
		_convert_timestamps(task_context)
		task_uuid = task_context['task_uuid']
		context_uuid = task_context['context_uuid']
		task = objects.Task.get(uuid=task_uuid)
		task.context_uuid = context_uuid
		task.update()
	if task_contexts:
		del data['task_context']

	task_goals = data.get('task_goal')
	for task_goal in task_goals or []:
		_replace_ids(task_goal, tasks_cache, 'task_id')
		_replace_ids(task_goal, goals_cache, 'goal_id')
		task_uuid = task_goal['task_uuid']
		goal_uuid = task_goal['goal_uuid']
		task = objects.Task.get(uuid=task_uuid)
		task.goal_uuid = goal_uuid
		task.update()
	if task_goals:
		del data['task_goal']

	# pokasowanie staroci
	_delete_missing(objects.Task, tasks_cache, file_sync_time)
	_delete_missing(objects.Folder, folders_cache, file_sync_time)
	_delete_missing(objects.Context, contexts_cache, file_sync_time)
	_delete_missing(objects.Tasknote, tasknotes_cache, file_sync_time)
	_delete_missing(objects.Alarm, alarms_cache, file_sync_time)

	c_last_sync.val = time.time()
	c_last_sync.save_or_update()

	c_last_sync.connection.commit()

	if data:
		_LOG.warn("Loader: remaining: %r", data.keys())
		_LOG.debug("Loader: remainig: %r", data)


def test():
	logging.basicConfig(level=logging.DEBUG,
			format='%(asctime)s %(levelname)-8s %(name)s - %(message)s')

	import db
	database = db.connect('wxgtd.db')
	print load_json(open('/home/k/GTD_SYNC.json').read())
	database.commit()

if __name__ == '__main__':
	test()
