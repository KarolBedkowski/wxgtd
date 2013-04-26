# -*- coding: utf-8 -*-

""" Database functions.

Copyright (c) Karol Będkowski, 2013

This file is part of wxGTD
Licence: GPLv2+
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2013"
__version__ = "2013-04-26"


import sqlite3
import logging

import sqlalchemy

from wxgtd.model import sqls
from wxgtd.model import objects

_LOG = logging.getLogger(__name__)


def connect(filename, debug=False, *args, **kwargs):
	""" Create connection  to database  & initiate it.

	Args:
		filename: path to sqlite database file
		debug: (bool) turn on  debugging
		args, kwargs: other arguments for sqlalachemy engine

	Return:
		Sqlalchemy Session class
	"""
	_LOG.info('connect %r', (filename, args, kwargs))
	engine = sqlalchemy.create_engine("sqlite:///" + filename, echo=debug,
			connect_args={'detect_types': sqlite3.PARSE_DECLTYPES |
				sqlite3.PARSE_COLNAMES}, native_datetime=True)
	for schema in sqls.SCHEMA_DEF:
		for sql in schema:
			engine.execute(sql)
	objects.Session.configure(bind=engine)
	objects.Base.metadata.create_all(engine)
	# bootstrap
	session = objects.Session()
	# 1. deviceId
	conf = session.query(objects.Conf).filter_by(key='deviceId').first()
	if conf is None:
		conf = objects.Conf(key='deviceId')
		conf.val = objects.generate_uuid()
		session.add(conf)
		_LOG.info('DB bootstrap: create deviceId=%r', conf.val)
		session.commit()
	# 2. cleanup
	engine.execute("delete from task_tags "
			"where task_uuid not in (select uuid from tasks)"
			"or tag_uuid not in (select uuid from tags)")
	return objects.Session
