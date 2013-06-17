#!/usr/bin/python
# -*- coding: utf-8 -*-
# pylint: disable=W0105

""" SqlAlchemy objects definition.

Copyright (c) Karol Będkowski, 2013

This file is part of wxGTD
Licence: GPLv2+
"""
__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2013"
__version__ = "2013-03-02"


import logging
import gettext
import uuid
import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import orm, or_, and_
from sqlalchemy import select, func

from wxgtd.model import enums

_LOG = logging.getLogger(__name__)
_ = gettext.gettext

# SQLAlchemy
Base = declarative_base()  # pylint: disable=C0103
Session = orm.sessionmaker()  # pylint: disable=C0103


def generate_uuid():
	""" Create uuid identifier.
	"""
	return str(uuid.uuid4())


class BaseModelMixin(object):
	""" Bazowy model - tworzenie kluczy, aktualizacja timestampów """

	def save(self):
		""" Save object into database. """
		session = Session.object_session(self) or Session()
		session.add(self)
		return session

	def load_from_dict(self, dict_):
		""" Update object attributes from dictionary. """
		for key, val in dict_.iteritems():
			if hasattr(self, key):
				setattr(self, key, val)

	def clone(self, cleanup=True):
		""" Clone current object.

		Args:
			cleanup: clean specific to instance values.
		"""
		newobj = type(self)()
		for prop in orm.object_mapper(self).iterate_properties:
			if isinstance(prop, orm.ColumnProperty) or \
					(isinstance(prop, orm.RelationshipProperty)
							and prop.secondary):
				setattr(newobj, prop.key, getattr(self, prop.key))
		if hasattr(newobj, 'uuid') and cleanup:
			newobj.uuid = None
		if hasattr(self, 'children'):
			for child in self.children:
				newobj.children.append(child.clone())
		return newobj

	def compare(self, obj):
		""" Compare objects. """
		for prop in orm.object_mapper(self).iterate_properties:
			if isinstance(prop, orm.ColumnProperty) or \
					(isinstance(prop, orm.RelationshipProperty)
							and prop.secondary):
				if getattr(obj, prop.key) != getattr(self, prop.key):
					return False
		return True

	def update_modify_time(self):
		if hasattr(self, 'modified'):
			self.modified = datetime.datetime.utcnow()  # pylint: disable=W0201

	@classmethod
	def selecy_by_modified_is_less(cls, timestamp, session=None):
		""" Find object with modified date less than given. """
		session = session or Session()
		return session.query(cls).filter(cls.modified < timestamp)

	@classmethod
	def select_old_usunsed(cls, timestamp, session=None):
		""" Find object with modified date less than given and nod used in
		any task. """
		session = session or Session()
		return session.query(cls).filter(cls.modified < timestamp).filter(
				~cls.tasks.any())

	@classmethod
	def all(cls, order_by=None, session=None):
		""" Return all objects this class.

		Args:
			order_by: optional order_by query argument
		"""
		session = session or Session()
		query = session.query(cls)
		if order_by:
			query = query.order_by(order_by)
		return query  # pylint: disable=E1101

	@classmethod
	def get(cls, session=None, **kwargs):
		""" Get one object with given attributes.

		Args:
			session: optional sqlalchemy session
			kwargs: query filters.

		Return:
			One object.
		"""
		return (session or Session()).query(cls).filter_by(
				**kwargs).first()

	def __repr__(self):
		info = []
		for prop in orm.object_mapper(self).iterate_properties:
			if isinstance(prop, orm.ColumnProperty) or \
					(isinstance(prop, orm.RelationshipProperty)
							and prop.secondary):
				info.append("%r=%r" % (prop.key, getattr(self, prop.key)))
		return "<" + self.__class__.__name__ + ' ' + ','.join(info) + ">"


class Task(BaseModelMixin, Base):
	""" Task.
	"""
	# pylint: disable=R0902

	__tablename__ = "tasks"

	uuid = Column(String(36), primary_key=True, default=generate_uuid)
	parent_uuid = Column(String(36), ForeignKey('tasks.uuid',
			onupdate="CASCADE", ondelete="SET NULL"), index=True)
	created = Column(DateTime, default=datetime.datetime.utcnow)
	modified = Column(DateTime, default=datetime.datetime.utcnow, index=True)
	completed = Column(DateTime)
	deleted = Column(DateTime)
	ordinal = Column(Integer, default=0)
	title = Column(String, index=True)
	note = Column(String)
	type = Column(Integer, nullable=False, default=enums.TYPE_TASK)
	starred = Column(Integer, default=0)
	status = Column(Integer, default=0)
	priority = Column(Integer, default=0)
	importance = Column(Integer, default=0)  # dla checlist pozycja
	start_date = Column(DateTime)
	start_time_set = Column(Integer, default=0)
	due_date = Column(DateTime, index=True)
	due_date_project = Column(DateTime)
	due_time_set = Column(Integer, default=0)
	due_date_mod = Column(Integer, default=0)
	floating_event = Column(Integer, default=0)
	duration = Column(Integer, default=0)  # czas trwania w minutach
	energy_required = Column(Integer, default=0)
	repeat_from = Column(Integer, default=0)
	repeat_pattern = Column(String)
	repeat_end = Column(Integer, default=0)
	hide_pattern = Column(String)
	hide_until = Column(DateTime)
	prevent_auto_purge = Column(Integer, default=0)
	trash_bin = Column(Integer, default=0)
	metainf = Column(String)
	alarm = Column(DateTime, index=True)
	alarm_pattern = Column(String)

	folder_uuid = Column(String(36), ForeignKey("folders.uuid",
			onupdate="CASCADE", ondelete="SET NULL"), index=True)
	context_uuid = Column(String(36), ForeignKey("contexts.uuid",
			onupdate="CASCADE", ondelete="SET NULL"), index=True)
	goal_uuid = Column(String(36), ForeignKey("goals.uuid",
			onupdate="CASCADE", ondelete="SET NULL"), index=True)

	folder = orm.relationship("Folder", backref=orm.backref('tasks'))
	context = orm.relationship("Context", backref=orm.backref('tasks'))
	goal = orm.relationship("Goal", backref=orm.backref('tasks'))
	tags = orm.relationship("TaskTag", cascade="all, delete, delete-orphan")
	children = orm.relationship("Task", backref=orm.backref('parent',
		remote_side=[uuid]))
	notes = orm.relationship("Tasknote", backref=orm.backref('tasks'),
			cascade="all, delete, delete-orphan")

	@property
	def status_name(self):
		return enums.STATUSES.get(self.status or 0, '?')

	def _get_task_completed(self):
		return bool(self.completed)

	def _set_task_completed(self, value):
		if value:
			if not self.completed:
				self.completed = datetime.datetime.utcnow()
		else:
			self.completed = None

	task_completed = property(_get_task_completed, _set_task_completed)
	""" Get/Set task completed flag.

	When setting task to completed, complete date is setting to current .
	"""

	@property
	def active_child_count(self):
		""" Count of not-complete subtask. """
		return orm.object_session(self).scalar(select([func.count(Task.uuid)])
				.where(and_(Task.parent_uuid == self.uuid,
						Task.completed.is_(None))))

	@property
	def child_overdue(self):
		""" Count of not-complete subtask with due date in past. """
		now = datetime.datetime.utcnow()
		return orm.object_session(self).scalar(select([func.count(Task.uuid)])
				.where(and_(Task.parent_uuid == self.uuid,
						Task.due_date.isnot(None), Task.completed.is_(None),
						or_(
							and_(Task.due_date < now,
								Task.type != enums.TYPE_PROJECT),
							and_(Task.due_date_project < now,
								Task.type == enums.TYPE_PROJECT)))))

	@property
	def overdue(self):
		""" Is task overdue. """
		if self.completed:
			return False
		now = datetime.datetime.utcnow()
		if self.type == enums.TYPE_PROJECT:
			return self.due_date_project and self.due_date_project < now
		return self.due_date and self.due_date < now

	@classmethod
	def select_by_filters(cls, params, session=None):
		""" Get tasks list according to given criteria.

		Args:
			params: dict with filter parameters (criteria)
			session: optional sqlalchemy session

		Returns:
			SqlAlchemy query
		"""
		# pylint: disable=R0912
		_LOG.debug('Task.select_by_filters(%r)', params)
		session = session or Session()
		query = session.query(cls)
		query = _append_filter_list(query, Task.context_uuid, params.get('contexts'))
		query = _append_filter_list(query, Task.folder_uuid, params.get('folders'))
		query = _append_filter_list(query, Task.goal_uuid, params.get('goals'))
		query = _append_filter_list(query, Task.status, params.get('statuses'))
		query = _append_filter_list(query, Task.type, params.get('types'))
		search_str = params.get('search_str', '').strip()
		if search_str:
			search_str = '%%' + search_str.lower() + "%%"
			query = query.filter(or_(func.lower(Task.title).like(search_str),
					func.lower(Task.note).like(search_str)))
		now = datetime.datetime.utcnow()
		query = _query_add_filter_by_tags(query, params)
		if params.get('hide_until'):
			# hide task with hide_until value in future
			query = query.filter(or_(Task.hide_until.is_(None),
					Task.hide_until <= now))
		if params.get('max_due_date'):
			query = query.filter(Task.due_date.isnot(None))
		elif params.get('no_due_date'):
			query = query.filter(Task.due_date.is_(None))
		query = _quert_add_filter_by_hotlist(query, params, now)
		query = _query_add_filter_by_finished(query, params.get('finished'))
		query = _query_add_filter_by_parent(query, params.get('parent_uuid'))
		# future alarms
		if params.get('active_alarm'):
			query = query.filter(Task.alarm >= now)
		query = query.order_by(Task.title)
		return query

	@classmethod
	def search(cls, text, active_only, session=None):
		""" Search for task with title/note matching text. """
		_LOG.debug('Task.search(%r, %r)', text, active_only)
		session = session or Session()
		query = session.query(cls)
		search_str = '%%' + text.lower() + "%%"
		query = query.filter(or_(func.lower(Task.title).like(search_str),
				func.lower(Task.note).like(search_str)))
		if active_only:
			query = query.filter(Task.completed.is_(None))
		query = query.order_by(Task.title)
		return query

	@classmethod
	def all_projects(cls):
		""" Get all projects from database. """
		# pylint: disable=E1101
		return Session().query(cls).filter_by(type=enums.TYPE_PROJECT)

	@classmethod
	def all_checklists(cls):
		""" Get all checklists from database. """
		# pylint: disable=E1101
		return Session().query(cls).filter_by(type=enums.TYPE_CHECKLIST)

	@classmethod
	def root_projects_checklists(cls, session=None):
		""" Get root projects and checklists. """
		session = session or Session()
		return (session.query(Task)
				.filter(Task.parent_uuid.is_(None),
						or_(Task.type == enums.TYPE_CHECKLIST,
						Task.type == enums.TYPE_PROJECT))
				.order_by(Task.title))

	@classmethod
	def select_reminders(cls, since=None, session=None):
		""" Get all not completed task with alarms from since (if given) to now.

		Args:
			since: optional datetime - minimal alarm time
			session: optional sqlalchemy session
		Returns:
			list of tasks with alarms
		"""
		_LOG.debug('Task.select_reminders(%r)', since)
		session = session or Session()
		query = session.query(cls)
		# with reminders in past
		now = datetime.datetime.utcnow()
		query = query.filter(Task.alarm <= now)
		# if "since" is set - use it as minimal alarm
		if since:
			query = query.filter(Task.alarm > since)
		# if "since" is set - use it as minimal alarm
		# not completed
		query = query.filter(Task.completed.is_(None))
		query = query.order_by(Task.alarm)
		return query

	@classmethod
	def find_max_importance(cls, parent_uuid, session=None):
		""" Find maximal importance in childs of given task."""
		return (session or Session()).scalar(
				select([func.max(Task.importance)]).where(
						Task.parent_uuid == parent_uuid)) or 0

	@property
	def child_count(self):
		"""  Count subtask. """
		return orm.object_session(self).scalar(select([func.count(Task.uuid)])
				.where(Task.parent_uuid == self.uuid))

	@property
	def sub_projects(self):
		return Session.object_session(self).query(Task).with_parent(self)\
				.filter_by(type=enums.TYPE_PROJECT)

	@property
	def sub_checklists(self):
		return Session.object_session(self).query(Task).with_parent(self)\
				.filter_by(type=enums.TYPE_CHECKLIST)

	@property
	def sub_project_or_checklists(self):
		return (Session.object_session(self).query(Task).with_parent(self)
				.filter(or_(Task.type == enums.TYPE_CHECKLIST,
						Task.type == enums.TYPE_PROJECT))
				.order_by(Task.title))

	def clone(self, cleanup=True):
		""" Clone current object. """
		newobj = BaseModelMixin.clone(self, cleanup)
		# clone tags
		for tasktag in self.tags:
			ntasktag = TaskTag()
			ntasktag.tag_uuid = tasktag.tag_uuid
			newobj.tags.append(ntasktag)
		# clone notes
		for note in self.notes:
			newobj.notes.append(note.clone())
		if cleanup:
			newobj.completed = None
		return newobj


def _append_filter_list(query, param, values):
	""" Build sqlalachemy filter object from params and values.

	Args:
		query: current sqlalchemy query object
		param: field in object (database column) used to filter
		values: values acceptable for given field

	Returns:
		Updated query object.
	"""
	if not values:
		# brak filtra
		return query
	if values == [None]:
		# wyświetlenie tylko bez ustawionej wartości parametru
		return query.filter(param.is_(None))
	elif None in values:
		# lista parametrów zawiera wartość NULL
		values = values[:]
		values.remove(None)
		return query.filter(or_(param.is_(None), param.in_(values)))
	# lista parametrów bez NULL
	return query.filter(param.in_(values))


def _query_add_filter_by_tags(query, params):
	""" Add filters related to tags. """
	if params.get('tags'):
		# filter by tags; pylint: disable=E1101
		tags = set(params.get('tags'))
		if None in tags:
			if len(tags) == 1:
				query = query.filter(~Task.tags.any())
			else:
				query = query.filter(or_(
						Task.tags.any(TaskTag.tag_uuid.in_(params['tags'])),
						~Task.tags.any()))
		else:
			query = query.filter(Task.tags.any(TaskTag.tag_uuid.in_(params['tags'])))
	return query


def _quert_add_filter_by_hotlist(query, params, now):
	""" Add filters related to hotlist. """
	opt = []
	if params.get('starred'):  # show starred task
		opt.append(Task.starred > 0)
	if params.get('min_priority') is not None:  # minimal task priority
		opt.append(Task.priority >= params['min_priority'])
	if params.get('max_due_date'):
		opt.append(or_(
			and_(Task.type != enums.TYPE_PROJECT,
					Task.due_date.isnot(None),
					Task.due_date <= params['max_due_date']),
			and_(Task.type == enums.TYPE_PROJECT,
					Task.due_date_project.isnot(None),
					Task.due_date_project <= params['max_due_date'])))
	if params.get('next_action'):
		opt.append(Task.status == 1)  # status = next action
	if params.get('started'):  # started task (with start date in past)
		opt.append(Task.start_date <= now)
	if opt:
		# use "or" or "and" operator for hotlist params
		if params.get('filter_operator', 'and') == 'or':
			query = query.filter(or_(*opt))  # pylint: disable=W0142
		else:
			query = query.filter(*opt)  # pylint: disable=W0142
	return query


def _query_add_filter_by_finished(query, finished):
	""" Add filters by completed to query. """
	if finished is not None:
		if finished:  # only finished
			query = query.filter(Task.completed.isnot(None))
		else:  # only not-completed
			query = query.filter(Task.completed.is_(None))
	return query


def _query_add_filter_by_parent(query, parent_uuid):
	""" Add filters by parent to query. """
	if parent_uuid is not None:
		if parent_uuid == 0:
			# filter by parent (show only master task (not subtask))
			query = query.filter(Task.parent_uuid.is_(None))
		elif parent_uuid:
			# filter by parent (show only subtask)
			query = query.filter(Task.parent_uuid == parent_uuid)
	return query


class Folder(BaseModelMixin, Base):
	""" Folder.


	Backref:
		- tasks
		- notebook_pages
	"""
	__tablename__ = "folders"

	uuid = Column(String(36), primary_key=True, default=generate_uuid)
	parent_uuid = Column(String(36), ForeignKey("folders.uuid",
			onupdate="CASCADE", ondelete="SET NULL"), index=True)
	created = Column(DateTime, default=datetime.datetime.utcnow)
	modified = Column(DateTime, default=datetime.datetime.utcnow, index=True)
	deleted = Column(DateTime)
	ordinal = Column(Integer, default=0)
	title = Column(String, index=True)
	note = Column(String)
	bg_color = Column(String, default="FFEFFF00")
	visible = Column(Integer, default=1)

	children = orm.relationship("Folder", backref=orm.backref('parent',
		remote_side=[uuid]))

	def save(self):
		if not self.uuid:
			self.uuid = str(uuid.uuid4())
		BaseModelMixin.save(self)


class Context(BaseModelMixin, Base):
	"""context"""
	__tablename__ = "contexts"
	uuid = Column(String(36), primary_key=True, default=generate_uuid)
	parent_uuid = Column(String(36), ForeignKey("contexts.uuid",
			onupdate="CASCADE", ondelete="SET NULL"), index=True)
	created = Column(DateTime, default=datetime.datetime.utcnow)
	modified = Column(DateTime, default=datetime.datetime.utcnow, index=True)
	deleted = Column(DateTime)
	ordinal = Column(Integer, default=0)
	title = Column(String, index=True)
	note = Column(String)
	bg_color = Column(String, default="FFEFFF00")
	visible = Column(Integer, default=1)

	children = orm.relationship("Context", backref=orm.backref('parent',
		remote_side=[uuid]))


class Tasknote(BaseModelMixin, Base):
	""" Task note object. """
	__tablename__ = "tasknotes"
	uuid = Column(String(36), primary_key=True, default=generate_uuid)
	task_uuid = Column(String(36), ForeignKey("tasks.uuid",
			onupdate="CASCADE", ondelete="SET NULL"), index=True)
	created = Column(DateTime, default=datetime.datetime.utcnow)
	modified = Column(DateTime, default=datetime.datetime.utcnow, index=True)
	ordinal = Column(Integer, default=0)
	title = Column(String, index=True)
	bg_color = Column(String, default="FFEFFF00")
	visible = Column(Integer, default=1)

	@classmethod
	def select_old_usunsed(cls, timestamp, session=None):
		""" Find object with modified date less than given and nod used in
		any task. """
		session = session or Session()
		return session.query(cls).filter(cls.task_uuid.is_(None))


class Goal(BaseModelMixin, Base):
	""" Goal """
	__tablename__ = "goals"
	uuid = Column(String(36), primary_key=True, default=generate_uuid)
	parent_uuid = Column(String(36), ForeignKey("goals.uuid",
			onupdate="CASCADE", ondelete="SET NULL"), index=True)
	created = Column(DateTime, default=datetime.datetime.utcnow)
	modified = Column(DateTime, default=datetime.datetime.utcnow, index=True)
	deleted = Column(DateTime)
	ordinal = Column(Integer, default=0)
	title = Column(String, index=True)
	note = Column(String)
	time_period = Column(Integer, default=0)
	archived = Column(Integer, default=0)
	bg_color = Column(String, default="FFEFFF00")
	visible = Column(Integer, default=1)

	children = orm.relationship("Goal", backref=orm.backref('parent',
		remote_side=[uuid]))


class Conf(Base):
	""" Internal configuration table  / object. """
	# pylint: disable=W0232, R0903

	__tablename__ = 'wxgtd'

	key = Column(String(50), primary_key=True)
	val = Column(String)


class Tag(BaseModelMixin, Base):
	""" Tag object. """

	__tablename__ = 'tags'
	uuid = Column(String(36), primary_key=True, default=generate_uuid)
	parent_uuid = Column(String(36), ForeignKey("tags.uuid",
			onupdate="CASCADE", ondelete="SET NULL"), index=True)
	created = Column(DateTime, default=datetime.datetime.utcnow)
	modified = Column(DateTime, default=datetime.datetime.utcnow, index=True)
	deleted = Column(DateTime)
	ordinal = Column(Integer, default=0)
	title = Column(String, index=True)
	note = Column(String)
	bg_color = Column(String, default="FFEFFF00")
	visible = Column(Integer, default=1)

	children = orm.relationship("Tag", backref=orm.backref('parent',
		remote_side=[uuid]))


class TaskTag(BaseModelMixin, Base):
	""" Association object for task and tags. """
	__tablename__ = "task_tags"
	task_uuid = Column(String(50), ForeignKey("tasks.uuid", onupdate="CASCADE",
			ondelete="CASCADE"), primary_key=True)
	tag_uuid = Column(String(50), ForeignKey("tags.uuid", onupdate="CASCADE",
			ondelete="CASCADE"), primary_key=True)
	created = Column(DateTime, default=datetime.datetime.utcnow)
	modified = Column(DateTime, default=datetime.datetime.utcnow, index=True)

	tag = orm.relationship("Tag", cascade="all", lazy="joined")


class NotebookPage(BaseModelMixin, Base):
	""" Notebook page. """

	__tablename__ = "notebook_pages"

	uuid = Column(String(36), primary_key=True, default=generate_uuid)
	created = Column(DateTime, default=datetime.datetime.utcnow)
	modified = Column(DateTime, default=datetime.datetime.utcnow, index=True)
	deleted = Column(DateTime)
	ordinal = Column(Integer, default=0)
	title = Column(String, index=True)
	note = Column(String)
	starred = Column(Integer, default=0)
	bg_color = Column(String, default="FFEFFF00")
	visible = Column(Integer, default=1)

	folder_uuid = Column(String(36), ForeignKey("folders.uuid",
			onupdate="CASCADE", ondelete="SET NULL"), index=True)

	folder = orm.relationship("Folder", backref=orm.backref('notebook_pages'))


class SyncLog(BaseModelMixin, Base):
	""" Synclog history """
	__tablename__ = "synclog"
	device_id = Column(String(50), primary_key=True)
	sync_time = Column(DateTime, primary_key=True)
	prev_sync_time = Column(DateTime)


Index('idx_task_childs', Task.parent_uuid, Task.due_date, Task.completed)
Index('idx_task_show', Task.hide_until, Task.parent_uuid, Task.completed,
		Task.title)
