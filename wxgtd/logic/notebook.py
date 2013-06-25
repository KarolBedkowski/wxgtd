#!/usr/bin/python
# -*- coding: utf-8 -*-
""" Various function that operate on Task (notebook pages) objects.

This file is part of wxGTD.
Copyright (c) Karol Będkowski, 2013
License: GPLv2+


"""
__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2013"
__version__ = "2013-05-28"

import logging
import gettext
import datetime


try:
	from wx.lib.pubsub.pub import Publisher
except ImportError:
	from wx.lib.pubsub import Publisher  # pylint: disable=E0611

from wxgtd.model import objects as OBJ

_LOG = logging.getLogger(__name__)
_ = gettext.gettext


def delete_notebook_page(page_uuid, session=None):
	""" Delete given notebook page.

	Show confirmation and delete page from database.

	Args:
		page_uuid: notebook page for delete
		session: sqlalchemy session

	Returns:
		True = task deleted
	"""
	session = session or OBJ.Session()
	page = session.query(OBJ.NotebookPage).filter_by(uuid=page_uuid).first()
	if not page:
		_LOG.warning("delete_notebook_page: missing page %r", page_uuid)
		return False
	page.deleted = datetime.datetime.now()
	session.commit()
	Publisher().sendMessage('notebook.delete', data={'notebook_uuid': page_uuid})
	return True


def save_modified_page(page, session=None):
	""" Save modified notebook page.
	Update required fields.

	Args:
		page: page to save
		session: optional SqlAlchemy session
	Returns:
		True if ok.
	"""
	session = session or OBJ.Session()
	page.update_modify_time()
	session.add(page)
	session.commit()
	Publisher().sendMessage('notebook.update', data={'notebook_uuid': page.uuid})
	return True
