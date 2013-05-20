# -*- coding: utf-8 -*-

""" Database functions.

Copyright (c) Karol Będkowski, 2013

This file is part of wxGTD
Licence: GPLv2+
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2013"
__version__ = "2013-04-26"


import time
import sqlite3
import logging

import sqlalchemy
from sqlalchemy.engine import Engine

from wxgtd.model import sqls
from wxgtd.model import objects

_LOG = logging.getLogger(__name__)


@sqlalchemy.event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_connection, _connection_record):
	cursor = dbapi_connection.cursor()
	cursor.execute("PRAGMA foreign_keys=ON")
	cursor.close()


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
	objects.Session.configure(bind=engine)  # pylint: disable=E1120

	if debug:
		@sqlalchemy.event.listens_for(Engine, "before_cursor_execute")
		def before_cursor_execute(_conn, _cursor,  # pylint: disable=W0612
				_stmt, _params, context, _executemany):
			context.app_query_start = time.time()

		@sqlalchemy.event.listens_for(Engine, "after_cursor_execute")
		def after_cursor_execute(_conn, _cursor,  # pylint: disable=W0612
				_stmt, _params, context, _executemany):
			_LOG.debug("Query time: %.02fms" % (
					(time.time() - context.app_query_start) * 1000))

	_LOG.info('Database create_all START')
	objects.Base.metadata.create_all(engine)
	_LOG.info('Database create_all COMPLETED')
	# bootstrap
	_LOG.info('Database bootstrap START')
	session = objects.Session()
	# 1. deviceId
	conf = session.query(  # pylint: disable=E1101
			objects.Conf).filter_by(key='deviceId').first()
	if conf is None:
		conf = objects.Conf(key='deviceId')
		conf.val = objects.generate_uuid()
		session.add(conf)  # pylint: disable=E1101
		_LOG.info('DB bootstrap: create deviceId=%r', conf.val)
		session.commit()  # pylint: disable=E1101
	_LOG.info('Database bootstrap cleanup')
	# 2. cleanup
	engine.execute("delete from task_tags "
			"where task_uuid not in (select uuid from tasks)"
			"or tag_uuid not in (select uuid from tags)")
	_LOG.info('Database bootstrap COMPLETED')

	return objects.Session
