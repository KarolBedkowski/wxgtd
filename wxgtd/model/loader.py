#!/usr/bin/python
# -*- coding: utf-8 -*-
# pylint: disable=W0141
""" Load data from GTD sync file format.

Copyright (c) Karol Będkowski, 2013

This file is part of wxGTD
Licence: GPLv2+
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2013"
__version__ = "2013-05-20"

import os
import logging
import zipfile
import gettext
import datetime
try:
	import cjson
	_JSON_DECODER = cjson.decode
	_JSON_ENCODER = cjson.encode
except ImportError:
	import json
	_JSON_DECODER = json.loads
	_JSON_ENCODER = json.dumps

from dateutil import parser, tz

from wxgtd.model import objects
from wxgtd.model import logic

_LOG = logging.getLogger(__name__)
_ = gettext.gettext


def _fake_update_func(*args, **kwargs):
	_LOG.info("progress %r %r", args, kwargs)


def load_from_file(filename, notify_cb=_fake_update_func, force=False):
	"""Load data from (zip)file.

	Args:
		filename: file to load
		notify_cb: function called in each step.
		force: don't check timestamps in synclog; always sync

	Returns:
		True if success.
	"""
	if not os.path.isfile(filename):
		notify_cb(50, _("File not found..."))
		return True
	notify_cb(0, _("Openning file"))
	if filename.endswith(".zip"):
		with zipfile.ZipFile(filename, "r") as zfile:
			fname = zfile.namelist()[0]
			return load_json(zfile.read(fname), notify_cb, force)
	else:
		with open(filename, "r") as ifile:
			return load_json(ifile.read(), notify_cb, force)
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
	_LOG.debug("_create_or_update(%r, %r)", cls, datadict.get("_id", datadict))
	uuid = datadict.pop("uuid")
	obj = session.query(cls).filter_by(uuid=uuid).first()
	if obj:
		modified = datadict.get("modified")
		if not modified or modified > obj.modified:
			# load only modified objs
			_LOG.debug('_create_or_update(%r, %r): update', cls, uuid)
			obj.load_from_dict(datadict)
	else:
		_LOG.debug('_create_or_update(%r, %r): create', cls, uuid)
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
	key_uuid = key_uuid or (key_id[:-2] + "uuid")
	res = None
	if key:
		uuid = cache.get(key)
		if uuid:
			res = objdict[key_uuid] = uuid
		else:
			_LOG.warn("missing key in cache %r", repr((objdict, key_id,
					key_uuid, key)))
	elif key is None:
		_LOG.warn("missing key %r", repr((objdict, key_id, key_uuid, key)))
	else:
		res = objdict[key_uuid] = None
	return res


def str2datetime_utc(string):
	""" Convert string like "2013-03-22T21:27:46.461Z" into timestamp.

	Args:
		string: string to convert

	Returns:
		Timestamp as long or None if error.
	"""
	if string and len(string) > 18:
		try:
			value = parser.parse(string)
			# convert to UTC
			value = value.astimezone(tz.tzutc())
			# remove timezone
			return value.replace(tzinfo=None)
		except ValueError:
			_LOG.exception("str2datetime_utc %r", string)
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
			value = str2datetime_utc(value)
		dictobj[field] = value or None

	for field in ("created", "modified", "deleted"):
		convert(field)
	for field in fields:
		convert(field)


def _cleanup_tasks(loaded_tasks, last_sync, session):
	""" Remove old (removed) tasks.
	Args:
		loaded_tasks: list of uuids loaded object to keep
		last_sync: items with modification older that this date will be deleted.
		session: SqlAlchemy session.
	Returns:
		number of deleted tasks.
	"""
	_LOG.info("_cleanup_tasks()")
	idx = 0
	for task in objects.Task.selecy_by_modified_is_less(last_sync,
			session=session):
		if task.uuid not in loaded_tasks:
			_LOG.info("_cleanup_tasks: delete task %r", task.uuid)
			session.delete(task)
			idx += 1
	return idx


def _cleanup_notebooks(loaded_notebooks, last_sync, session):
	""" Remove old (removed) notebook pages.
	Args:
		loaded_tasks: list of uuids loaded object to keep
		last_sync: items with modification older that this date will be deleted.
		session: SqlAlchemy session.
	Returns:
		number of deleted pages.
	"""
	_LOG.info("_cleanup_notebooks()")
	idx = 0
	for page in objects.NotebookPage.selecy_by_modified_is_less(last_sync,
			session=session):
		if page.uuid not in loaded_notebooks:
			_LOG.info("_cleanup_notebooks: delete page %r", page.uuid)
			session.delete(page)
			idx += 1
	return idx


def _cleanup_unused(objcls, loaded_cache, last_sync, session):
	""" Remove old (removed) and not used folders.
	Args:
		objcls: class object to search & delete
		loaded_cache: cache with uuids loaded object to keep
		last_sync: items with modification older that this date will be deleted.
		session: SqlAlchemy session.
	Returns:
		number of deleted objects.
	"""
	_LOG.info("_cleanup_unused(%r)", objcls)
	loaded = set(loaded_cache.itervalues())
	idx = 0
	for obj in objcls.select_old_usunsed(last_sync,
			session=session):
		if obj.uuid not in loaded:
			_LOG.debug("_cleanup_unused: delete  %r", obj.uuid)
			session.delete(obj)
			idx += 1
	_LOG.info("_cleanup_unused(%r): deleted=%d", objcls, idx)
	return idx


def _build_id_uuid_map(objects_list):
	""" Build dict that map id to uuid.

	Args:
		objects_list: list of dict containing loaded objects.

	Returns:
		Dict[id->uuid] for all objects.
	"""
	cache = {}
	for obj in objects_list or []:
		uuid = obj.get("uuid")
		oid = obj.get("_id")
		if uuid and oid:
			cache[oid] = uuid
	return cache


def _check_synclog(data, session):
	""" Check synclog for last modification.
	"""
	last_sync_log = session.query(objects.SyncLog).order_by(
			objects.SyncLog.sync_time.desc()).first()
	print last_sync_log
	if last_sync_log is None:
		return True

	last_file_sync_time = datetime.datetime(1900, 1, 1)
	for synclog in data.get("syncLog") or []:
		file_sync_time_str = synclog.get("syncTime")
		file_sync_time = str2datetime_utc(file_sync_time_str)
		if last_file_sync_time < file_sync_time:
			last_file_sync_time = file_sync_time

	if last_file_sync_time > last_sync_log.sync_time:
		_LOG.info("_check_synclog need sync %r, %r", last_file_sync_time,
				last_sync_log.sync_time),
		return True
	return False


def sort_objects_by_parent(objs):
	""" Sort objects by parent.
	Put first object with no parent. Then object with known parent (already
	existing in result objects). Etc.
	"""
	if not objs:
		return []
	all_objs_count = len(objs)
	# no parent
	result = filter(lambda x: x["parent_id"] == 0, objs)
	result_uuids = set(obj["_id"] for obj in result)
	objs = filter(lambda x: x["parent_id"] != 0, objs)
	# rest
	while objs:
		objs_to_add = filter(lambda x: x["parent_id"] in result_uuids, objs)
		objs = filter(lambda x: x["parent_id"] not in result_uuids, objs)
		result.extend(objs_to_add)
		result_uuids.update(obj["_id"] for obj in objs_to_add)
	assert len(result) == all_objs_count
	return result


def load_json(strdata, notify_cb, force=False):
	""" Load data from json string.

	Args:
		strdata: json-encoded data
		notify_cb: function called on each step.

	Returns:
		true if success.
	"""
	notify_cb(2, _("Decoding.."))
	data = _JSON_DECODER(strdata.decode("UTF-8"))
	session = objects.Session()

	notify_cb(5, _("Checking..."))
	if not force and not _check_synclog(data, session):
		notify_cb(2, _("Don't load"))
		_LOG.info("load_json: no loading file")
		return True

	# load
	folders_cache = _load_folders(data, session, notify_cb)
	contexts_cache = _load_contexts(data, session, notify_cb)
	goals_cache = _load_goals(data, session, notify_cb)
	tasks_cache = _load_tasks(data, session, notify_cb)
	tasknotes_cache = _load_tasknotes(data, session, tasks_cache, notify_cb)
	_load_alarms(data, session, tasks_cache, notify_cb)
	_load_task_folders(data, session, tasks_cache, folders_cache, notify_cb)
	_load_task_contexts(data, session, tasks_cache, contexts_cache, notify_cb)
	_load_task_goals(data, session, tasks_cache, goals_cache, notify_cb)
	tags_cache = _load_tags(data, session, notify_cb)
	_load_task_tags(data, session, tasks_cache, tags_cache, notify_cb)
	notebooks_cache = _load_notebooks(data, session, notify_cb)
	_load_notebook_folders(data, session, notebooks_cache, folders_cache,
			notify_cb)
	last_prev_sync_time = _load_synclog(data, session, notify_cb)

	# cleanup
	if last_prev_sync_time:
		notify_cb(84, _("Cleanup"))
		# pokasowanie staroci
		deleted_cnt = _cleanup_tasks(set(tasks_cache.itervalues()),
				last_prev_sync_time, session)
		notify_cb(85, _("Removed tasks: %d") % deleted_cnt)
		deleted_cnt = _cleanup_unused(objects.Folder, folders_cache,
				last_prev_sync_time, session)
		notify_cb(86, _("Removed folders: %d") % deleted_cnt)
		deleted_cnt = _cleanup_unused(objects.Context, contexts_cache,
				last_prev_sync_time, session)
		notify_cb(87, _("Removed contexts: %d") % deleted_cnt)
		deleted_cnt = _cleanup_unused(objects.Tasknote, tasknotes_cache,
				last_prev_sync_time, session)
		notify_cb(88, _("Removed task notes: %d") % deleted_cnt)
		deleted_cnt = _cleanup_unused(objects.Goal, goals_cache,
				last_prev_sync_time, session)
		notify_cb(89, _("Removed goals %d") % deleted_cnt)
		deleted_cnt = _cleanup_notebooks(set(notebooks_cache.itervalues()),
				last_prev_sync_time, session)
		notify_cb(85, _("Removed notebook pages: %d") % deleted_cnt)
		# TODO: renumeracja

	notify_cb(90, _("Committing..."))
	session.commit()  # pylint: disable=E1101
	notify_cb(100, _("Load completed"))

	if data:
		_LOG.warn("Loader: remaining: %r", data.keys())
		_LOG.debug("Loader: remainig: %r", data)
	return True


def _load_folders(data, session, notify_cb):
	_LOG.info("_load_folders")
	notify_cb(6, _("Loading folders"))
	folders = data.get("folder")
	folders_cache = _build_id_uuid_map(folders)
	for folder in sort_objects_by_parent(folders):  # musi być sortowane,
		# bo nie znajdzie parenta
		_replace_ids(folder, folders_cache, "parent_id")
		_convert_timestamps(folder)
		_create_or_update(session, objects.Folder, folder)
	if folders:
		del data["folder"]
	notify_cb(10, _("Loaded %d folders") % len(folders_cache))
	return folders_cache


def _load_contexts(data, session, notify_cb):
	_LOG.info("_load_contexts")
	notify_cb(11, _("Loading contexts"))
	contexts = data.get("context")
	contexts_cache = _build_id_uuid_map(contexts)
	for context in sort_objects_by_parent(contexts):
		_replace_ids(context, contexts_cache, "parent_id")
		_convert_timestamps(context)
		_create_or_update(session, objects.Context, context)
	if contexts:
		del data["context"]
	notify_cb(15, _("Loaded %d contexts") % len(contexts_cache))
	return contexts_cache


def _load_goals(data, session, notify_cb):
	_LOG.info("_load_goals")
	notify_cb(16, _("Loading goals"))
	goals = data.get("goal")
	goals_cache = _build_id_uuid_map(goals)
	for goal in sort_objects_by_parent(goals):
		_replace_ids(goal, goals_cache, "parent_id")
		_convert_timestamps(goal)
		_create_or_update(session, objects.Goal, goal)
	if goals:
		del data["goal"]
	notify_cb(20, _("Loaded %d goals") % len(goals_cache))
	return goals_cache


def _load_tasks(data, session, notify_cb):
	_LOG.info("_load_tasks")
	notify_cb(21, _("Loading tasks"))
	tasks = data.get("task")
	tasks_cache = _build_id_uuid_map(tasks)
	for task in sort_objects_by_parent(tasks):
		_replace_ids(task, tasks_cache, "parent_id")
		_convert_timestamps(task, "completed", "start_date", "due_date",
				"due_date_project", "hide_until")
		task["context_uuid"] = None
		task["folder_uuid"] = None
		task["goal_uuid"] = None
		task_obj = _create_or_update(session, objects.Task, task)
		logic.update_task_hide(task_obj)
	if tasks:
		del data["task"]
	notify_cb(38, _("Loaded %d tasks") % len(tasks_cache))
	return tasks_cache


def _load_tasknotes(data, session, tasks_cache, notify_cb):
	_LOG.info("_load_tasknotes")
	notify_cb(39, _("Loading task notes"))
	tasknotes = data.get("tasknote")
	tasknotes_cache = _build_id_uuid_map(tasknotes)
	for tasknote in tasknotes or []:
		_replace_ids(tasknote, tasks_cache, "task_id")
		_convert_timestamps(tasknote)
		_create_or_update(session, objects.Tasknote, tasknote)
	if tasknotes:
		del data["tasknote"]
	notify_cb(43, _("Loaded %d task notes") % len(tasknotes_cache))
	return tasknotes_cache


def _load_alarms(data, session, tasks_cache, notify_cb):
	_LOG.info("_load_alarms")
	notify_cb(44, _("Loading alarms"))
	alarms = data.get("alarm") or []
	for alarm in alarms:
		task_uuid = _replace_ids(alarm, tasks_cache, "task_id")
		if not task_uuid:
			_LOG.error("load alarm error %r; %r; %r", alarm, task_uuid)
			continue
		_convert_timestamps(alarm, "alarm")
		task = session.query(  # pylint: disable=E1101
				objects.Task).filter_by(uuid=task_uuid).first()
		if task.modified <= alarm["modified"]:
			task.alarm = alarm["alarm"]
			logic.update_task_alarm(task)
		else:
			_LOG.debug("skip %r", alarm)
	if alarms:
		del data["alarm"]
	notify_cb(46, _("Loaded %d alarms") % len(alarms))


def _load_task_folders(data, session, tasks_cache, folders_cache, notify_cb):
	_LOG.info("_load_task_folders")
	notify_cb(47, _("Loading task folders"))
	task_folders = data.get("task_folder") or []
	for task_folder in task_folders:
		task_uuid = _replace_ids(task_folder, tasks_cache, "task_id")
		folder_uuid = _replace_ids(task_folder, folders_cache, "folder_id")
		if not task_uuid or not folder_uuid:
			_LOG.error("load task folder error %r; %r; %r", task_folder,
					task_uuid, folder_uuid)
			continue
		_convert_timestamps(task_folder)
		task = session.query(  # pylint: disable=E1101
				objects.Task).filter_by(uuid=task_uuid).first()
		if task.modified <= task_folder["modified"]:
			task.folder_uuid = folder_uuid
		else:
			_LOG.debug("skip %r", task_folder)
	if task_folders:
		del data["task_folder"]
	notify_cb(51, _("Loaded %d task folders") % len(task_folders))


def _load_task_contexts(data, session, tasks_cache, contexts_cache,
		notify_cb):
	_LOG.info("_load_task_contexts")
	notify_cb(52, _("Loading task contexts"))
	task_contexts = data.get("task_context") or []
	for task_context in task_contexts:
		task_uuid = _replace_ids(task_context, tasks_cache, "task_id")
		context_uuid = _replace_ids(task_context, contexts_cache, "context_id")
		if not task_uuid or not context_uuid:
			_LOG.error("load task contexts error %r; %r; %r", task_context,
					task_uuid, context_uuid)
			continue
		_convert_timestamps(task_context)
		task = session.query(  # pylint: disable=E1101
				objects.Task).filter_by(uuid=task_uuid).first()
		if task.modified <= task_context["modified"]:
			task.context_uuid = context_uuid
		else:
			_LOG.debug("skip %r", task_context)
	if task_contexts:
		del data["task_context"]
	notify_cb(56, _("Loaded %d tasks contexts") % len(task_contexts))


def _load_task_goals(data, session, tasks_cache, goals_cache, notify_cb):
	_LOG.info("_load_task_goals")
	notify_cb(57, _("Loading task goals"))
	task_goals = data.get("task_goal") or []
	for task_goal in task_goals:
		task_uuid = _replace_ids(task_goal, tasks_cache, "task_id")
		goal_uuid = _replace_ids(task_goal, goals_cache, "goal_id")
		if not task_uuid or not goal_uuid:
			_LOG.error("load task goal error %r; %r; %r", task_goal,
					task_uuid, goal_uuid)
			continue
		_convert_timestamps(task_goal)
		task = session.query(  # pylint: disable=E1101
				objects.Task).filter_by(uuid=task_uuid).first()
		if task.modified <= task_goal["modified"]:
			task.goal_uuid = goal_uuid
		else:
			_LOG.debug("skip %r", task_goal)
	if task_goals:
		del data["task_goal"]
	notify_cb(61, _("Loaded %d task goals") % len(task_goals))


def _load_tags(data, session, notify_cb):
	_LOG.info("_load_tags")
	notify_cb(62, _("Loading tags"))
	tags = data.get("tag")
	tags_cache = _build_id_uuid_map(tags)
	for tag in sort_objects_by_parent(tags):
		_replace_ids(tag, tags_cache, "parent_id")
		_convert_timestamps(tag)
		_create_or_update(session, objects.Tag, tag)
	if tags:
		del data["tag"]
	notify_cb(66, _("Loaded %d tags") % len(tags_cache))
	return tags_cache


def _load_task_tags(data, session, tasks_cache, tags_cache, notify_cb):
	_LOG.info("_load_task_tags")
	notify_cb(67, _("Loading task tags"))
	task_tags = data.get("task_tag") or []
	for task_tag in task_tags:
		task_uuid = _replace_ids(task_tag, tasks_cache, "task_id")
		tag_uuid = _replace_ids(task_tag, tags_cache, "tag_id")
		_convert_timestamps(task_tag)
		obj = session.query(  # pylint: disable=E1101
				objects.TaskTag).filter_by(task_uuid=task_uuid,
				tag_uuid=tag_uuid).first()
		if obj:
			modified = task_tag.get("modified")
			if not modified or not obj.modified or modified > obj.modified:
				obj.load_from_dict(task_tag)
		else:
			obj = objects.TaskTag(task_uuid=task_uuid, tag_uuid=tag_uuid)
			obj.load_from_dict(task_tag)
			session.add(obj)  # pylint: disable=E1101
	if task_tags:
		del data["task_tag"]
	notify_cb(71, _("Loaded %d task tags") % len(task_tags))


def _load_notebooks(data, session, notify_cb):
	_LOG.info("_load_notebooks")
	notify_cb(16, _("Loading notebooks"))
	notebooks = data.get("notebook") or []
	notebooks_cache = _build_id_uuid_map(notebooks)
	for notebook in notebooks:
		_convert_timestamps(notebook)
		notebook['folder_uuid'] = None
		_create_or_update(session, objects.NotebookPage, notebook)
	if notebooks:
		del data["notebook"]
	notify_cb(20, _("Loaded %d notebook pages") % len(notebooks_cache))
	return notebooks_cache


def _load_notebook_folders(data, session, notebooks_cache, folders_cache,
		notify_cb):
	_LOG.info("_load_notebook_folders")
	notify_cb(47, _("Loading notebook pages folders"))
	notebook_folders = data.get("notebook_folder") or []
	for notebook_folder in notebook_folders:
		notebook_uuid = _replace_ids(notebook_folder, notebooks_cache,
				"notebook_id")
		folder_uuid = _replace_ids(notebook_folder, folders_cache, "folder_id")
		if not notebook_uuid or not folder_uuid:
			_LOG.error("load notebook folder error %r; %r; %r", notebook_folder,
					notebook_uuid, folder_uuid)
			continue
		_convert_timestamps(notebook_folder)
		notebook = session.query(  # pylint: disable=E1101
				objects.NotebookPage).filter_by(uuid=notebook_uuid).first()
		if notebook.modified <= notebook_folder["modified"]:
			notebook.folder_uuid = folder_uuid
		else:
			_LOG.debug("skip %r", notebook_folder)
	if notebook_folders:
		del data["notebook_folder"]
	notify_cb(51, _("Loaded %d notebook folders") % len(notebook_folders))


def _load_synclog(data, session, notify_cb):
	_LOG.info("_load_synclog")
	notify_cb(72, _("Loading synclog"))
	last_sync_time = last_prev_sync_time = datetime.datetime(1900, 1, 1)
	for sync_log in data.get("syncLog"):
		_convert_timestamps(sync_log, "prevSyncTime", "syncTime")
		slog_item = objects.SyncLog.get(session, device_id=sync_log["deviceId"])
		if slog_item:
			slog_item.prev_sync_time = slog_item.sync_time
		else:
			slog_item = objects.SyncLog()
			slog_item.device_id = sync_log["deviceId"]
		slog_item.sync_time = sync_log["syncTime"]
		session.add(slog_item)  # pylint: disable=E1101
		if slog_item.sync_time > last_sync_time:
			last_sync_time = slog_item.sync_time
			last_prev_sync_time = slog_item.prev_sync_time
	if "syncLog" in data:
		del data["syncLog"]
	return last_prev_sync_time


def test():
	logging.basicConfig(level=logging.DEBUG,
			format="%(asctime)s %(levelname)-8s %(name)s - %(message)s")

	from wxgtd.model import db
	db.connect("wxgtd.db")
	print load_json(open("/home/k/GTD_SYNC.json").read(), _fake_update_func)

if __name__ == "__main__":
	test()
