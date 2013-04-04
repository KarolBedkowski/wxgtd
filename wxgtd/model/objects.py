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
import time

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import orm

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
		self.modified = self.created = time.time()
		session = Session.object_session(self) or Session()
		session.add(self)
		return session

	def update(self):
		self.modified = time.time()
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
		- tagi
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
			self.completed = time.time()
		else:
			self.completed = None

	task_completed = property(_get_task_completed, _set_task_completed)

	@classmethod
	def get_stared(cls):
		return cls.select(stared=1)

	@classmethod
	def get_finished(cls):
		return cls.select(where_stmt="completed is not null")

	@classmethod
	def select_by_filters(cls, contexts, folders, goals, statuses, types,
			parent_uuid, starred, min_priority, max_start_date,
			max_due_date, finished, tags):
		session = Session()
		query = session.query(cls)
		if contexts:
			if contexts == [None]:
				query = query.filter(Task.context_uuid.is_(None))
			else:
				query = query.filter(Task.context_uuid.in_(contexts))
		if folders:
			if folders == [None]:
				query = query.filter(Task.folder_uuid.is_(None))
			else:
				query = query.filter(Task.folder_uuid.in_(folders))
		# TODO: tags, goals
		if statuses:
			if statuses == [None]:
				query = query.filter(Task.status.is_(None))
			else:
				query = query.filter(Task.status.in_(statuses))
		if starred:
			query = query.filter_by(starred > 0)
		if min_priority is not None:
			query = query.filter(Task.priority >= min_priority)
#		if max_start_date:
#			where_stmt.append('start_date <= %d' % max_start_date)
#		if max_due_date:
#			where_stmt.append('due_date <= %d' % max_due_date)
#		if finished is not None:
#			if finished:
#				where_stmt.append("(completed<>'' and completed is not null)")
#			else:
#				where_stmt.append("(completed='' or completed is null)")
		if parent_uuid == 0:
			query = query.filter(Task.parent_uuid.is_(None))
		elif parent_uuid:
			query = query.filter(Task.parent_uuid == parent_uuid)
		return query.all()

	@classmethod
	def all_projects(cls):
		return cls.select(type=TYPE_PROJECT)


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
		self.modified = self.created = time.time()
		BaseModelMixin.save(self)

	def update(self):
		self.modified = time.time()
		BaseModelMixin.update(self)


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
