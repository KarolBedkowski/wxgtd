#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Obiekty

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
from sqlalchemy import orm, or_

import enums

_LOG = logging.getLogger(__name__)
_ = gettext.gettext


# SQLAlchemy
Base = declarative_base()
Session = orm.sessionmaker()


def _gen_uuid():
	return str(uuid.uuid4())


class BaseModelMixin(object):
	""" Bazowy model - tworzenie kluczy, aktualizacja timestampów """

	def save(self):
		session = Session.object_session(self) or Session()
		session.add(self)
		return session

	@classmethod
	def selecy_by_modified_is_less(cls, timestamp):
		session = Session()
		return session.query(cls).filter(cls.modified < timestamp).all()

	@classmethod
	def all(cls):
		session = Session()
		return session.query(cls).all()

	def load_from_dict(self, dict_):
		for key, val in dict_.iteritems():
			if hasattr(self, key):
				setattr(self, key, val)

	@classmethod
	def get(cls, session=None, **kwargs):
		return (session or Session()).query(cls).filter_by(
				**kwargs).first()


class Task(BaseModelMixin, Base):
	"""Task

	TODO:
		- importance - nie używane (?)
	"""
	__tablename__ = "tasks"

	uuid = Column(String(36), primary_key=True, default=_gen_uuid)
	parent_uuid = Column(String(36), ForeignKey('tasks.uuid'))
	created = Column(DateTime, default=datetime.datetime.now)
	modified = Column(DateTime, default=datetime.datetime.now)
	completed = Column(DateTime)
	deleted = Column(DateTime)
	ordinal = Column(Integer)
	title = Column(String)
	note = Column(String)
	type = Column(Integer)
	starred = Column(Integer)
	status = Column(Integer)
	priority = Column(Integer)
	importance = Column(Integer)
	start_date = Column(DateTime)
	start_time_set = Column(Integer)
	due_date = Column(DateTime)
	due_date_project = Column(DateTime)
	due_time_set = Column(Integer)
	due_date_mod = Column(Integer)
	floating_even = Column(Integer)
	duration = Column(Integer)
	energy_required = Column(Integer)
	repeat_from = Column(Integer)
	repeat_pattern = Column(String)
	repeat_end = Column(Integer)
	hide_pattern = Column(String)
	hide_until = Column(DateTime)
	prevent_auto_purge = Column(Integer)
	trash_bin = Column(Integer)
	metainf = Column(String)
	alarm = Column(DateTime)
	alarm_pattern = Column(String)

	folder_uuid = Column(String(36), ForeignKey("folders.uuid"))
	context_uuid = Column(String(36), ForeignKey("contexts.uuid"))
	goal_uuid = Column(String(36), ForeignKey("goals.uuid"))

	folder = orm.relationship("Folder")
	context = orm.relationship("Context")
	goal = orm.relationship("Goal")
	tags = orm.relationship("TaskTag", cascade="all, delete-orphan")
	children = orm.relationship("Task", backref=orm.backref('parent',
		remote_side=[uuid]))
	notes = orm.relationship("Tasknote", cascade="all, delete-orphan")

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

	@classmethod
	def get_finished(cls):
		return cls.select(where_stmt="completed is not null")

	@classmethod
	def select_by_filters(cls, params):
		session = Session()
		query = session.query(cls)
		query = _append_filter_list(query, Task.context_uuid, params.get('contexts'))
		query = _append_filter_list(query, Task.folder_uuid, params.get('folders'))
		query = _append_filter_list(query, Task.goal_uuid, params.get('goals'))
		query = _append_filter_list(query, Task.status, params.get('statuses'))
		query = _append_filter_list(query, Task.type, params.get('types'))
		now = datetime.datetime.now()
		if params.get('tags'):
			query = query.filter(Task.tags.any(TaskTag.task_uuid.in_(params['tags'])))
		if params.get('hide_until'):
			query = query.filter(or_(Task.hide_until.is_(None),
					Task.hide_until <= now))
		# params hotlist
		opt = []
		if params.get('starred'):
			opt.append(Task.starred > 0)
		if params.get('min_priority') is not None:
			opt.append(Task.priority >= params('min_priority'))
		if params.get('max_due_date'):
			opt.append(Task.due_date <= params['max_due_date'])
		if params.get('next_action'):
			opt.append(Task.status == 1)  # next action
		if params.get('started'):
			opt.append(Task.start_date <= now)
		if opt:
			if params.get('filter_operator', 'and') == 'or':
				query = query.filter(or_(*opt))
			else:
				query = query.filter(*opt)
		finished = params.get('finished')
		if finished is not None:
			if finished:
				# zakończone
				query = query.filter(Task.completed.isnot(None))
			else:
				# niezakończone
				query = query.filter(Task.completed.is_(None))
		parent_uuid = params.get('parent_uuid')
		if parent_uuid is not None:
			if parent_uuid == 0:
				query = query.filter(Task.parent_uuid.is_(None))
			elif parent_uuid:
				query = query.filter(Task.parent_uuid == parent_uuid)
		query = query.options(orm.joinedload(Task.context)) \
				.options(orm.joinedload(Task.folder)) \
				.options(orm.joinedload(Task.goal)) \
				.order_by(Task.title)
		return query.all()

	@classmethod
	def all_projects(cls):
		return Session().query(cls).filter_by(type=enums.TYPE_PROJECT).all()


def _append_filter_list(query, param, values):
	""" Dodanie do query filtra dla atrybutu param dla wartości z listy values
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
	"""folder"""
	__tablename__ = "folders"

	uuid = Column(String(36), primary_key=True, default=_gen_uuid)
	parent_uuid = Column(String(36), ForeignKey("folders.uuid"))
	created = Column(DateTime, default=datetime.datetime.now)
	modified = Column(DateTime, default=datetime.datetime.now)
	deleted = Column(DateTime)
	ordinal = Column(Integer)
	title = Column(String)
	note = Column(String)
	color = Column(String)
	visible = Column(Integer)

	children = orm.relationship("Folder", backref=orm.backref('parent',
		remote_side=[uuid]))

	def save(self):
		if not self.uuid:
			self.uuid = str(uuid.uuid4())
		BaseModelMixin.save(self)


class Context(BaseModelMixin, Base):
	"""context"""
	__tablename__ = "contexts"
	uuid = Column(String(36), primary_key=True, default=_gen_uuid)
	parent_uuid = Column(String(36), ForeignKey("contexts.uuid"))
	created = Column(DateTime, default=datetime.datetime.now)
	modified = Column(DateTime, default=datetime.datetime.now)
	deleted = Column(DateTime)
	ordinal = Column(Integer)
	title = Column(String)
	note = Column(String)
	color = Column(String)
	visible = Column(Integer)

	children = orm.relationship("Context", backref=orm.backref('parent',
		remote_side=[uuid]))


class Tasknote(BaseModelMixin, Base):
	"""tasknote"""
	__tablename__ = "tasknotes"
	uuid = Column(String(36), primary_key=True, default=_gen_uuid)
	task_uuid = Column(String(36), ForeignKey("tasks.uuid"))
	created = Column(DateTime, default=datetime.datetime.now)
	modified = Column(DateTime, default=datetime.datetime.now)
	ordinal = Column(Integer)
	title = Column(String)
	color = Column(String)
	visible = Column(Integer)


class Goal(BaseModelMixin, Base):
	""" Goal """
	__tablename__ = "goals"
	uuid = Column(String(36), primary_key=True, default=_gen_uuid)
	parent_uuid = Column(String(36), ForeignKey("goals.uuid"))
	created = Column(DateTime, default=datetime.datetime.now)
	modified = Column(DateTime, default=datetime.datetime.now)
	deleted = Column(DateTime)
	ordinal = Column(Integer)
	title = Column(String)
	note = Column(String)
	time_period = Column(Integer)
	archived = Column(Integer)
	color = Column(String)
	visible = Column(Integer)

	children = orm.relationship("Goal", backref=orm.backref('parent',
		remote_side=[uuid]))


class Conf(Base):
	__tablename__ = 'wxgtd'
	key = Column(String(50), primary_key=True)
	val = Column(String)


class Tag(BaseModelMixin, Base):
	""" Obiekt tag.
	Task może mieć wiele tagów."""

	__tablename__ = 'tags'
	uuid = Column(String(36), primary_key=True, default=_gen_uuid)
	parent_uuid = Column(String(36), ForeignKey("tags.uuid"))
	created = Column(DateTime, default=datetime.datetime.now)
	modified = Column(DateTime, default=datetime.datetime.now)
	deleted = Column(DateTime)
	ordinal = Column(Integer)
	title = Column(String)
	note = Column(String)
	bg_color = Column(String)
	visible = Column(Integer)

	children = orm.relationship("Tag", backref=orm.backref('parent',
		remote_side=[uuid]))


class TaskTag(BaseModelMixin, Base):
	__tablename__ = "task_tags"
	task_uuid = Column(String(50), ForeignKey("tasks.uuid"), primary_key=True)
	tag_uuid = Column(String(50), ForeignKey("tags.uuid"), primary_key=True)
	modified = Column(DateTime, onupdate=datetime.datetime.now)
	deleted = Column(DateTime)

	tag = orm.relationship("Tag", cascade="all")
