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

_LOG = logging.getLogger(__name__)
_ = gettext.gettext

STATUSES = {0: _("No Status"),  # no status
		1: _("Next Action"),
		2: _("Active"),
		3: _("Planning"),
		4: _("Delegated"),
		5: _("Waiting"),
		6: _("Hold"),
		7: _("Postponed"),
		8: _("Someday"),
		9: _("Canceled"),
		10: _("Reference")}

TYPE_TASK = 0
TYPE_PROJECT = 1
TYPE_CHECKLIST = 2
TYPE_CHECKLIST_ITEM = 3

TYPES = {TYPE_TASK: _("Task"),
		TYPE_PROJECT: _("Project"),
		TYPE_CHECKLIST: _("Checklist"),
		TYPE_CHECKLIST_ITEM: _("Checklist Item"),
		4: _("Note"),
		5: _("Call"),
		6: _("Email"),
		7: _("SMS"),
		8: _("Return Call")}


# SQLAlchemy
Base = declarative_base()
Session = orm.sessionmaker()


class BaseModelMixin(object):
	""" Bazowy model - tworzenie kluczy, aktualizacja timestampów """

	def save(self):
		if not self.uuid:
			self.uuid = str(uuid.uuid4())
		if not self.created:
			self.modified = self.created = datetime.datetime.now()
		else:
			self.modified = datetime.datetime.now()
		session = Session.object_session(self) or Session()
		session.add(self)
		return session

	def update(self):
		self.modified = datetime.datetime.now()
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

	uuid = Column(String(36), primary_key=True)
	parent_uuid = Column(String(36), ForeignKey('tasks.uuid'))
	created = Column(DateTime)
	modified = Column(DateTime)
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

	folder_uuid = Column(String(36), ForeignKey("folders.uuid"))
	context_uuid = Column(String(36), ForeignKey("contexts.uuid"))
	goal_uuid = Column(String(36), ForeignKey("goals.uuid"))

	folder = orm.relationship("Folder")
	context = orm.relationship("Context")
	goal = orm.relationship("Goal")
	tags = orm.relationship("TaskTag")
	children = orm.relationship("Task", backref=orm.backref('parent',
		remote_side=[uuid]))
	notes = orm.relationship("Tasknote")
	alarms = orm.relationship("Alarm")

	@property
	def status_name(self):
		return STATUSES.get(self.status or 0, '?')

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
	def select_by_filters(cls, contexts, folders, goals, statuses, types,
			parent_uuid, starred, min_priority, max_start_date,
			max_due_date, finished, tags):
		session = Session()
		query = session.query(cls)
		query = _append_filter_list(query, Task.context_uuid, contexts)
		query = _append_filter_list(query, Task.folder_uuid, folders)
		query = _append_filter_list(query, Task.goal_uuid, goals)
		query = _append_filter_list(query, Task.status, statuses)
		query = _append_filter_list(query, Task.type, types)
		if tags:
			query = query.filter(Task.tags.any(TaskTag.task_uuid.in_(tags)))
		if starred:
			query = query.filter(starred > 0)
		if min_priority is not None:
			query = query.filter(Task.priority >= min_priority)
		if max_start_date:
			query = query.filter(Task.start_date <= max_start_date)
		if max_due_date:
			query = query.filter(Task.due_date <= max_due_date)
		if finished is not None:
			if finished:
				query = query.filter(Task.completed.isnot(None))
			else:
				query = query.filter(Task.completed.is_(None))
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
		return Session().query(cls).filter_by(type=TYPE_PROJECT).all()


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

	uuid = Column(String(36), primary_key=True)
	parent_uuid = Column(String(36), ForeignKey("folders.uuid"))
	created = Column(DateTime)
	modified = Column(DateTime)
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
	uuid = Column(String(36), primary_key=True)
	parent_uuid = Column(String(36), ForeignKey("contexts.uuid"))
	created = Column(DateTime)
	modified = Column(DateTime)
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
	uuid = Column(String(36), primary_key=True)
	task_uuid = Column(String(36), ForeignKey("tasks.uuid"))
	created = Column(DateTime)
	modified = Column(DateTime)
	ordinal = Column(Integer)
	title = Column(String)
	color = Column(String)
	visible = Column(Integer)


class Alarm(BaseModelMixin, Base):
	"""alarm"""

	__tablename__ = "alarms"
	uuid = Column(String(36), primary_key=True)
	task_uuid = Column(String(36), ForeignKey("tasks.uuid"))
	created = Column(DateTime)
	modified = Column(DateTime)
	alarm = Column(DateTime)
	reminder = Column(Integer)
	active = Column(Integer)
	note = Column(String)


class Goal(BaseModelMixin, Base):
	""" Goal """
	__tablename__ = "goals"
	uuid = Column(String(36), primary_key=True)
	parent_uuid = Column(String(36), ForeignKey("goals.uuid"))
	created = Column(DateTime)
	modified = Column(DateTime)
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
	uuid = Column(String(36), primary_key=True)
	parent_uuid = Column(String(36), ForeignKey("tags.uuid"))
	created = Column(DateTime)
	modified = Column(DateTime)
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
	modified = Column(DateTime)
	deleted = Column(DateTime)

	tag = orm.relationship("Tag")
