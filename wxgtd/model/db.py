# -*- coding: utf-8 -*-

"""
Obiekt bazy dany - dostęp do danych

TODO: przenieść całe tworzenie obiektów z sqlite
"""
from __future__ import with_statement

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2009-2013"
__version__ = "2011-05-15"


import sqlite3
import logging
import uuid

import sqlalchemy

import sqls
import objects

_LOG = logging.getLogger(__name__)


def connect(filename, *args, **kwargs):
	_LOG.info('connect %r', (filename, args, kwargs))
	engine = sqlalchemy.create_engine("sqlite:///" + filename, echo=True,
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
		conf.val = str(uuid.uuid4())
		session.add(conf)
		_LOG.info('DB bootstrap: create deviceId=%r', conf.val)
		session.commit()
	return objects.Session
