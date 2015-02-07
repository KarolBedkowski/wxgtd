# -*- coding: utf-8 -*-

""" Database functions.

Copyright (c) Karol Będkowski, 2013

This file is part of wxGTD
Licence: GPLv2+
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2013"
__version__ = "2013-04-26"


import os
import time
import sqlite3
import logging
import datetime

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
	sqls.fix_synclog(engine)
	objects.Session.configure(bind=engine)  # pylint: disable=E1120

	if debug:
		@sqlalchemy.event.listens_for(Engine, "before_cursor_execute")
		def before_cursor_execute(_conn, _cursor,  # pylint: disable=W0612
				_stmt, _params, context, _executemany):
			context.app_query_start = time.time()

		@sqlalchemy.event.listens_for(Engine, "after_cursor_execute")
		def after_cursor_execute(_conn, _cursor,  # pylint: disable=W0612
				_stmt, _params, context, _executemany):
			_LOG.debug("Query time: %.02fms",
					(time.time() - context.app_query_start) * 1000)

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

	date_threshold = datetime.datetime.now() - datetime.timedelta(days=90)
	_LOG.debug('Cleanup deleted tasks older than %r', date_threshold)
	engine.execute("delete from tasks "
			"where deleted < ? and prevent_auto_purge = 0",
			(date_threshold, ))
	_LOG.debug('Cleanup deleted folders older than %r', date_threshold)
	engine.execute("delete from folders where deleted < ?", (date_threshold, ))

	_LOG.debug('Cleanup deleted goals older than %r', date_threshold)
	engine.execute("delete from goals where deleted < ?", (date_threshold, ))

	_LOG.debug('Cleanup deleted tags older than %r', date_threshold)
	engine.execute("delete from tags where deleted < ?", (date_threshold, ))

	_LOG.debug('Cleanup deleted pages older than %r', date_threshold)
	engine.execute("delete from notebook_pages where deleted < ?",
			(date_threshold, ))

	_LOG.debug("Cleanup synclog")
	wrong_sls = engine.execute('select device_id, sync_time from synclog s '
				'where sync_time < (select max(sync_time) '
				'from synclog s2 where s.device_id = s2.device_id)').fetchall()
	for wrong_sl in wrong_sls:
		_LOG.debug('  delete synclog: %r', wrong_sls)
		engine.execute("delete from synclog where device_id=? and sync_time=?",
				 (wrong_sls[0], wrong_sls[1]))

	_LOG.info('Database bootstrap COMPLETED')
	return objects.Session


def find_db_file(config):
	""" Find existing database file. """

	def _try_path(path):
		""" Check if in given path exists wxgtd.db file. """
		file_path = os.path.join(path, 'wxgtd.db')
		if os.path.isfile(file_path):
			return file_path
		return None

	db_filename = _try_path(config.main_dir)
	if not db_filename:
		db_filename = _try_path(os.path.join(config.main_dir, 'db'))
	if not db_filename:
		db_dir = os.path.join(config.main_dir, 'db')
		if os.path.isdir(db_dir):
			db_filename = os.path.join(db_dir, 'wxgtd.db')
	if not db_filename:
		db_filename = os.path.join(config.user_share_dir, 'wxgtd.db')
	#  create dir for database if not exist
	db_dirname = os.path.dirname(db_filename)
	if not os.path.isdir(db_dirname):
		os.mkdir(db_dirname)
	return db_filename
