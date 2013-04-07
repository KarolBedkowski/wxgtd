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
import datetime

import objects
import logic

_LOG = logging.getLogger(__name__)


def load_from_file(filename):
	"""Load data from zipfile"""
	if filename.endswith('.zip'):
		with zipfile.ZipFile(filename, 'r') as zfile:
			fname = zfile.namelist()[0]
			load_json(zfile.read(fname))
	else:
		with open(filename, 'r') as ifile:
			load_json(ifile.read())


def _create_or_update(session, cls, datadict, cache=None):
	oid = datadict.pop('_id')
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
	if cache is not None:
		cache[oid] = uuid
		cache[uuid] = oid
	return obj


def _replace_ids(objdict, cache, key_id, key_uuid=None):
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
	""" Convert timestamps like '2013-03-22T21:27:46.461Z'"""
	if string and len(string) > 18:
		try:
			return time.mktime(time.strptime(string[:19], "%Y-%m-%dT%H:%M:%S"))
		except:
			_LOG.exception("str2timestamp %r", string)


def _convert_timestamps(dictobj, *fields):
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
	data = cjson.decode(strdata.decode('UTF-8'))
	session = objects.Session()

	last_sync = 0
	c_last_sync = session.query(objects.Conf).filter_by(key='last_sync').first()
	if c_last_sync:
		last_sync = c_last_sync.val
	else:
		c_last_sync = objects.Conf(key='last_sync')

	file_sync_time_str = data.get('syncLog')[0].get('syncTime')
	file_sync_time = str2timestamp(file_sync_time_str)

	if last_sync > file_sync_time:
		_LOG.info("no loading file time=%r, last sync=%r", last_sync,
				file_sync_time_str)

	_LOG.info("load_json: folder")
	folders_cache = {}
	folders = data.get('folder')
	for folder in sorted(folders or []):  # musi być sortowane,
		# bo nie znajdzie parenta
		_replace_ids(folder, folders_cache, 'parent_id')
		_convert_timestamps(folder)
		_create_or_update(session, objects.Folder, folder, folders_cache)
	if folders:
		del data['folder']

	_LOG.info("load_json: context")
	contexts_cache = {}
	contexts = data.get('context')
	for context in sorted(contexts or []):
		_replace_ids(context, contexts_cache, 'parent_id')
		_convert_timestamps(context)
		_create_or_update(session, objects.Context, context, contexts_cache)
	if contexts:
		del data['context']

	# Goals
	_LOG.info("load_json: goals")
	goals = data.get('goal')
	goals_cache = {}
	for goal in sorted(goals or []):
		_replace_ids(goal, goals_cache, 'parent_id')
		_convert_timestamps(goal)
		_create_or_update(session, objects.Goal, goal, goals_cache)
	if goal:
		del data['goal']

	_LOG.info("load_json: tasks")
	tasks_cache = {}
	tasks = data.get('task')
	for task in sorted(tasks or []):
		_replace_ids(task, tasks_cache, 'parent_id')
		_convert_timestamps(task, 'completed', 'start_date', 'due_date',
				'due_date_project', 'hide_until')
		task['context_uuid'] = None
		task['folder_uuid'] = None
		task['goal_uuid'] = None
		task_obj = _create_or_update(session, objects.Task, task, tasks_cache)
		logic.update_task_hide(task_obj)
	if tasks:
		del data['task']

	_LOG.info("load_json: tasknote")
	tasknotes_cache = {}
	tasknotes = data.get('tasknote')
	for tasknote in tasknotes or []:
		_replace_ids(tasknote, tasks_cache, 'task_id')
		_convert_timestamps(tasknote)
		_create_or_update(session, objects.Tasknote, tasknote, tasknotes_cache)
	if tasknotes:
		del data['tasknote']

	_LOG.info("load_json: alarms")
	alarms = data.get('alarm')
	for alarm in alarms or []:
		task_uuid = _replace_ids(alarm, tasks_cache, 'task_id')
		_convert_timestamps(alarm, 'alarm')
		task = session.query(objects.Task).filter_by(uuid=task_uuid).first()
		task.alarm = alarm['alarm']
		logic.update_task_alarm(task)
	if alarms:
		del data['alarm']

	_LOG.info("load_json: task_folder")
	task_folders = data.get('task_folder')
	for task_folder in task_folders or []:
		task_uuid = _replace_ids(task_folder, tasks_cache, 'task_id')
		folder_uuid = _replace_ids(task_folder, folders_cache, 'folder_id')
		_convert_timestamps(task_folder)
		task = session.query(objects.Task).filter_by(uuid=task_uuid).first()
		task.folder_uuid = folder_uuid
	if task_folders:
		del data['task_folder']

	_LOG.info("load_json: task_contexts")
	task_contexts = data.get('task_context')
	for task_context in task_contexts or []:
		task_uuid = _replace_ids(task_context, tasks_cache, 'task_id')
		context_uuid = _replace_ids(task_context, contexts_cache, 'context_id')
		_convert_timestamps(task_context)
		task = session.query(objects.Task).filter_by(uuid=task_uuid).first()
		task.context_uuid = context_uuid
	if task_contexts:
		del data['task_context']

	_LOG.info("load_json: task_goal")
	task_goals = data.get('task_goal')
	for task_goal in task_goals or []:
		task_uuid = _replace_ids(task_goal, tasks_cache, 'task_id')
		goal_uuid = _replace_ids(task_goal, goals_cache, 'goal_id')
		task = session.query(objects.Task).filter_by(uuid=task_uuid).first()
		task.goal_uuid = goal_uuid
	if task_goals:
		del data['task_goal']

	# tagi
	_LOG.info("load_json: tag")
	tags = data.get('tag')
	tags_cache = {}
	for tag in sorted(tags or []):
		_replace_ids(tag, tags_cache, 'parent_id')
		_convert_timestamps(tag)
		_create_or_update(session, objects.Tag, tag, tags_cache)
	if tags:
		del data['tag']

	_LOG.info("load_json: task_tag")
	# TODO: dodać do sorm obsługe many2many i przerobić to
	task_tags = data.get('task_tag')
	for task_tag in task_tags or []:
		task_uuid = _replace_ids(task_tag, tasks_cache, 'task_id')
		tag_uuid = _replace_ids(task_tag, tags_cache, 'tag_id')
		_convert_timestamps(task_tag)
		obj = session.query(objects.TaskTag).filter_by(task_uuid=task_uuid,
				tag_uuid=tag_uuid).first()
		if obj:
			modified = task_tag.get('modified')
			if not modified or modified > obj.modified:
				obj.load_from_dict(task_tag)
		else:
			obj = objects.TaskTag(task_uuid=task_uuid, tag_uuid=tag_uuid)
			obj.load_from_dict(task_tag)
			session.add(obj)
	if task_tags:
		del data['task_tag']

	_LOG.info("load_json: czyszczenie")
	# pokasowanie staroci
	_delete_missing(objects.Task, tasks_cache, file_sync_time)
	_delete_missing(objects.Folder, folders_cache, file_sync_time)
	_delete_missing(objects.Context, contexts_cache, file_sync_time)
	_delete_missing(objects.Tasknote, tasknotes_cache, file_sync_time)

	c_last_sync.val = time.time()

	session.commit()

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
