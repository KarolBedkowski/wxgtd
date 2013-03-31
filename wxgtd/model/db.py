# -*- coding: utf-8 -*-

"""
Obiekt bazy dany - dostęp do danych

TODO: przenieść całe tworzenie obiektów z sqlite
"""
from __future__ import with_statement

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2009-2013"
__version__ = "2011-05-15"


import logging
import uuid

import sorm
import sqls
import objects

_LOG = logging.getLogger(__name__)


def connect(*argv, **kwargs):
	dbconn = sorm.DbConnection()
	dbconn.open(*argv, **kwargs)
	with dbconn.get_cursor() as cursor:
		for schema in sqls.SCHEMA_DEF:
			for sql in schema:
				cursor.executescript(sql)
	# bootstrap
	# 1. deviceId
	conf = objects.Conf.get(key='deviceId')
	if conf is None:
		conf = objects.Conf(key='deviceId')
		conf.val = str(uuid.uuid4())
		conf.save()
		_LOG.info('DB bootstrap: create deviceId=%r', conf.val)
		dbconn.commit()
	return dbconn
