#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
import cjson
import zipfile
import time

import objects

_LOG = logging.getLogger()


def load_from_zip(filename):
	"""Load data from zipfile"""
	with zipfile.ZipFile(filename, 'r') as zfile:
		load_json(zfile.read())


def _create_or_update(cls, datadict, cache=None):
	oid = datadict.pop('_id')
	uuid = datadict.pop('uuid')
	obj = cls.get(uuid=uuid)
	if obj:
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
			_LOG.warn('missing key in cache %r', repr((objdict, key_id, key_uuid)))
	else:
		_LOG.warn('missing key %r', repr((objdict, key_id, key_uuid)))


def _convert_timestamps(dictobj, *fields):
	def convert(field):
		value = dictobj.get(field)
		if value:
			try:
				val = time.mktime(time.strptime(value[:19], "%Y-%m-%dT%H:%M:%S"))
				dictobj[field] = val
			except:
				_LOG.exception("_convert_timestamps %r=%r", field, value)

	for field in ('created', 'modified', 'deleted'):
		convert(field)
	for field in fields:
		convert(field)


def load_json(strdata):
	data = cjson.decode(strdata)

	folders_cache = {}
	folders = data.get('folder')
	for folder in folders or []:
		_replace_ids(folder, folders_cache, 'parent_id')
		_convert_timestamps(folder)
		_create_or_update(objects.Folder, folder, folders_cache)

	contexts_cache = {}
	contexts = data.get('context')
	for context in contexts or []:
		_replace_ids(context, contexts_cache, 'parent_id')
		_convert_timestamps(context)
		_create_or_update(objects.Context, context, contexts_cache)

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

	tasknotes = data.get('tasknote')
	for tasknote in tasknotes or []:
		_replace_ids(tasknote, tasks_cache, 'task_id')
		_convert_timestamps(tasknote)
		_create_or_update(objects.Tasknote, tasknote)

	alarms = data.get('alarm')
	for alarm in alarms or []:
		_replace_ids(alarm, tasks_cache, 'task_id')
		_convert_timestamps(alarm, 'alarm')
		_create_or_update(objects.Alarm, alarm)

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


def test():
	logging.basicConfig(level=logging.DEBUG,
			format='%(asctime)s %(levelname)-8s %(name)s - %(message)s')

	import db
	database = db.connect('wxgtd.db')
	print load_json(open('/home/k/GTD_SYNC.json').read())
	database.commit()

if __name__ == '__main__':
	test()
