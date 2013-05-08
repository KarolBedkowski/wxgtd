#!/usr/bin/python
# -*- coding: utf-8 -*-

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

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import orm, or_, and_
from sqlalchemy import select, func

from wxgtd.model import enums

_LOG = logging.getLogger(__name__)
_ = gettext.gettext

# SQLAlchemy
Base = declarative_base()
Session = orm.sessionmaker()


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

	def clone(self):
		""" Clone current object. """
		newobj = type(self)()
		for prop in orm.object_mapper(self).iterate_properties:
			if isinstance(prop, orm.ColumnProperty) or \
					(isinstance(prop, orm.RelationshipProperty)
							and prop.secondary):
				setattr(newobj, prop.key, getattr(self, prop.key))
		return newobj

	@classmethod
	def selecy_by_modified_is_less(cls, timestamp):
		""" Find object with modified date less than given. """
		session = Session()
		return session.query(cls).filter(cls.modified < timestamp).all()

	@classmethod
	def all(cls):
		""" Return all objects this class. """
		session = Session()
		return session.query(cls).all()

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
	__tablename__ = "tasks"

	uuid = Column(String(36), primary_key=True, default=generate_uuid)
	parent_uuid = Column(String(36), ForeignKey('tasks.uuid'))
	created = Column(DateTime, default=datetime.datetime.now)
	modified = Column(DateTime, onupdate=datetime.datetime.now)
	completed = Column(DateTime)
	deleted = Column(DateTime)
	ordinal = Column(Integer, default=0)
	title = Column(String)
	note = Column(String)
	type = Column(Integer, nullable=False)
	starred = Column(Integer, default=0)
	status = Column(Integer, default=0)
	priority = Column(Integer, default=0)
	importance = Column(Integer, default=0)  # dla checlist pozycja
	start_date = Column(DateTime)
	start_time_set = Column(Integer, default=0)
	due_date = Column(DateTime)
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
	alarm = Column(DateTime)
	alarm_pattern = Column(String)

	folder_uuid = Column(String(36), ForeignKey("folders.uuid"))
	context_uuid = Column(String(36), ForeignKey("contexts.uuid"))
	goal_uuid = Column(String(36), ForeignKey("goals.uuid"))

	folder = orm.relationship("Folder")
	context = orm.relationship("Context")
	goal = orm.relationship("Goal")
	tags = orm.relationship("TaskTag", cascade="all, delete, delete-orphan")
	children = orm.relationship("Task", backref=orm.backref('parent',
		remote_side=[uuid]))
	notes = orm.relationship("Tasknote", cascade="all, delete, delete-orphan")

	@property
	def status_name(self):
		return enums.STATUSES.get(self.status or 0, '?')

	def _get_task_completed(self):
		return bool(self.completed)

	def _set_task_completed(self, value):
		if value:
			self.completed = datetime.datetime.now()
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
		now = datetime.datetime.now()
		return orm.object_session(self).scalar(select([func.count(Task.uuid)])
				.where(and_(Task.parent_uuid == self.uuid,
						Task.due_date.isnot(None), Task.due_date < now,
						Task.completed.is_(None))))

	@classmethod
	def select_by_filters(cls, params, session=None):
		""" Get tasks list according to given criteria.

		Args:
			params: dict with filter parameters (criteria)
			sessoin: optional sqlalchemy session

		Returns:
			list of task
		"""
		session = session or Session()
		query = session.query(cls)
		query = _append_filter_list(query, Task.context_uuid, params.get('contexts'))
		query = _append_filter_list(query, Task.folder_uuid, params.get('folders'))
		query = _append_filter_list(query, Task.goal_uuid, params.get('goals'))
		query = _append_filter_list(query, Task.status, params.get('statuses'))
		query = _append_filter_list(query, Task.type, params.get('types'))
		search_str = params.get('search_str', '').strip()
		if search_str:
			search_str = '%%' + search_str + "%%"
			query = query.filter(or_(Task.title.like(search_str),
					Task.note.like(search_str)))
		now = datetime.datetime.now()
		if params.get('tags'):
			# filter by tags
			query = query.filter(Task.tags.any(TaskTag.task_uuid.in_(params['tags'])))
		if params.get('hide_until'):
			# hide task with hide_until value in future
			query = query.filter(or_(Task.hide_until.is_(None),
					Task.hide_until <= now))
		# params hotlistd
		opt = []
		if params.get('starred'):  # show starred task
			opt.append(Task.starred > 0)
		if params.get('min_priority') is not None:  # minimal task priority
			opt.append(Task.priority >= params['min_priority'])
		if params.get('max_due_date'):
			opt.append(Task.due_date <= params['max_due_date'])
		if params.get('next_action'):
			opt.append(Task.status == 1)  # status = next action
		if params.get('started'):  # started task (with start date in past)
			opt.append(Task.start_date <= now)
		if opt:
			# use "or" or "and" operator for hotlist params
			if params.get('filter_operator', 'and') == 'or':
				query = query.filter(or_(*opt))
			else:
				query = query.filter(*opt)
		finished = params.get('finished')  # filter by completed value
		if finished is not None:
			if finished:  # only finished
				query = query.filter(Task.completed.isnot(None))
			else:  # only not-completed
				query = query.filter(Task.completed.is_(None))
		parent_uuid = params.get('parent_uuid')
		if parent_uuid is not None:
			if parent_uuid == 0:
				# filter by parent (show only master task (not subtask))
				query = query.filter(Task.parent_uuid.is_(None))
			elif parent_uuid:
				# filter by parent (show only subtask)
				query = query.filter(Task.parent_uuid == parent_uuid)
		# future alarms
		if params.get('active_alarm'):
			query = query.filter(Task.alarm >= now)
		query = query.options(orm.joinedload(Task.context)) \
				.options(orm.joinedload(Task.folder)) \
				.options(orm.joinedload(Task.goal)) \
				.options(orm.subqueryload(Task.tags)) \
				.order_by(Task.title)
		return query.all()

	@classmethod
	def all_projects(cls):
		""" Get all projects from database. """
		return Session().query(cls).filter_by(type=enums.TYPE_PROJECT).all()

	@classmethod
	def all_checklists(cls):
		""" Get all checklists from database. """
		return Session().query(cls).filter_by(type=enums.TYPE_CHECKLIST).all()

	@classmethod
	def select_remainders(cls, since=None, session=None):
		""" Get all not completed task with alarms from since (if given) to now.

		Args:
			since: optional datetime - minimal alarm time
			session: optional sqlalchemy session
		Returns:
			list of tasks with alarms
		"""
		session = session or Session()
		query = session.query(cls)
		# with reminders in past
		now = datetime.datetime.now()
		query = query.filter(Task.alarm <= now)
		# if "since" is set - use it as minimal alarm
		if since:
			query = query.filter(Task.alarm > since)
		# if "since" is set - use it as minimal alarm
		# not completed
		query = query.filter(Task.completed.is_(None))
		query = query.options(orm.joinedload(Task.context)) \
				.options(orm.joinedload(Task.folder)) \
				.options(orm.joinedload(Task.goal)) \
				.options(orm.subqueryload(Task.tags)) \
				.order_by(Task.title)
		return query.all()

	@property
	def child_count(self):
		"""  Count subtask. """
		return orm.object_session(self).scalar(select([func.count(Task.uuid)])
				.where(Task.parent_uuid == self.uuid))

	def clone(self):
		""" Clone current object. """
		newobj = BaseModelMixin.clone(self)
		# clone tags
		for tasktag in self.tags:
			ntasktag = TaskTag()
			ntasktag.tag_uuid = tasktag.tag_uuid
			newobj.tags.append(ntasktag)
		# clone notes
		for note in self.notes:
			newobj.notes.append(note.clone())
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


class Folder(BaseModelMixin, Base):
	""" Folder. """
	__tablename__ = "folders"

	uuid = Column(String(36), primary_key=True, default=generate_uuid)
	parent_uuid = Column(String(36), ForeignKey("folders.uuid"))
	created = Column(DateTime, default=datetime.datetime.now)
	modified = Column(DateTime, onupdate=datetime.datetime.now)
	deleted = Column(DateTime)
	ordinal = Column(Integer, default=0)
	title = Column(String)
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
	parent_uuid = Column(String(36), ForeignKey("contexts.uuid"))
	created = Column(DateTime, default=datetime.datetime.now)
	modified = Column(DateTime, onupdate=datetime.datetime.now)
	deleted = Column(DateTime)
	ordinal = Column(Integer, default=0)
	title = Column(String)
	note = Column(String)
	bg_color = Column(String, default="FFEFFF00")
	visible = Column(Integer, default=1)

	children = orm.relationship("Context", backref=orm.backref('parent',
		remote_side=[uuid]))


class Tasknote(BaseModelMixin, Base):
	""" Task note object. """
	__tablename__ = "tasknotes"
	uuid = Column(String(36), primary_key=True, default=generate_uuid)
	task_uuid = Column(String(36), ForeignKey("tasks.uuid"))
	created = Column(DateTime, default=datetime.datetime.now)
	modified = Column(DateTime, onupdate=datetime.datetime.now)
	ordinal = Column(Integer, default=0)
	title = Column(String)
	bg_color = Column(String, default="FFEFFF00")
	visible = Column(Integer, default=1)


class Goal(BaseModelMixin, Base):
	""" Goal """
	__tablename__ = "goals"
	uuid = Column(String(36), primary_key=True, default=generate_uuid)
	parent_uuid = Column(String(36), ForeignKey("goals.uuid"))
	created = Column(DateTime, default=datetime.datetime.now)
	modified = Column(DateTime, onupdate=datetime.datetime.now)
	deleted = Column(DateTime)
	ordinal = Column(Integer, default=0)
	title = Column(String)
	note = Column(String)
	time_period = Column(Integer, default=0)
	archived = Column(Integer, default=0)
	bg_color = Column(String, default="FFEFFF00")
	visible = Column(Integer, default=1)

	children = orm.relationship("Goal", backref=orm.backref('parent',
		remote_side=[uuid]))


class Conf(Base):
	""" Internal configuration table  / object. """
	__tablename__ = 'wxgtd'
	key = Column(String(50), primary_key=True)
	val = Column(String)


class Tag(BaseModelMixin, Base):
	""" Tag object. """

	__tablename__ = 'tags'
	uuid = Column(String(36), primary_key=True, default=generate_uuid)
	parent_uuid = Column(String(36), ForeignKey("tags.uuid"))
	created = Column(DateTime, default=datetime.datetime.now)
	modified = Column(DateTime, onupdate=datetime.datetime.now)
	deleted = Column(DateTime)
	ordinal = Column(Integer, default=0)
	title = Column(String)
	note = Column(String)
	bg_color = Column(String, default="FFEFFF00")
	visible = Column(Integer, default=1)

	children = orm.relationship("Tag", backref=orm.backref('parent',
		remote_side=[uuid]))


class TaskTag(BaseModelMixin, Base):
	""" Association object for task and tags. """
	__tablename__ = "task_tags"
	task_uuid = Column(String(50), ForeignKey("tasks.uuid"), primary_key=True)
	tag_uuid = Column(String(50), ForeignKey("tags.uuid"), primary_key=True)
	created = Column(DateTime, default=datetime.datetime.now)
	modified = Column(DateTime, onupdate=datetime.datetime.now)

	tag = orm.relationship("Tag", cascade="all", lazy="joined")
