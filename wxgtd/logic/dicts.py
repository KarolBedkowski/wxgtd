#!/usr/bin/python
# -*- coding: utf-8 -*-
""" Various function that operate on dictionaries (goals, folders, etc)

This file is part of wxGTD.
Copyright (c) Karol Będkowski, 2013
License: GPLv2+


"""
__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2013"
__version__ = "2013-04-19"


import logging

try:
	from wx.lib.pubsub.pub import Publisher
except ImportError:
	from wx.lib.pubsub import Publisher  # pylint: disable=E0611

from wxgtd.model import objects as obj


_LOG = logging.getLogger(__name__)


def find_or_create_goal(title, session):
	""" Find goal with given title, if not found - create it.

	Args:
		title: title of goal
		session: SqlAlchemy session

	Returns:
		Goal object
	"""
	goal = obj.Goal.get(session, title=title)
	if not goal:
		_LOG.debug('find_or_create_goal: creating goal from title=%r',
				title)
		goal = obj.Goal(title=title)
		session.add(goal)
		Publisher().sendMessage('goal.update')
	return goal


def find_or_create_folder(title, session):
	""" Find folder with given title, if not found - create it.

	Args:
		title: title of folder
		session: SqlAlchemy session

	Returns:
		Folder object
	"""
	folder = obj.Folder.get(session, title=title)
	if not folder:
		_LOG.debug('find_or_create_folder: creating folder from title=%r',
				title)
		folder = obj.Folder(title=title)
		session.add(folder)
		Publisher().sendMessage('folder.update')
	return folder


def find_or_create_context(title, session):
	""" Find context with given title, if not found - create it.

	Args:
		title: title of context
		session: SqlAlchemy session

	Returns:
		Context object
	"""
	context = obj.Context.get(session, title=title)
	if not context:
		_LOG.debug('find_or_create_context: creating context from title=%r',
				title)
		context = obj.Context(title=title)
		session.add(context)
		Publisher().sendMessage('context.update')
	return context
