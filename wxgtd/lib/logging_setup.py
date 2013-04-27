#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
""" Logging setup.
Copyright (c) Karol Będkowski, 2013

This file is part of wxGTD
Licence: GPLv2+
"""
__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2013"
__version__ = "2013-04-27"

import sys
import os.path
import logging
import tempfile
import time

from . import appconfig


class ColorFormatter(logging.Formatter):
	""" Formatter for logs that color messages according to level. """
	COLORS = {'DEBUG': 34,
			'INFO': 37,
			'WARNING': 33,
			'ERROR': 31,
			'CRITICAL': 31}
	FORMAT_SEQ = "\033[1;%dm%s\033[0m"

	def format(self, record):
		record.levelname = self.FORMAT_SEQ % (
				self.COLORS.get(record.levelname, 37), record.levelname)
		return logging.Formatter.format(self, record)


def logging_setup(filename, debug=False, debug_sql=False):
	""" Setup configuration.

	Args:
		filename: log file name
		debug: (bool) set more messages
		debug_sql: (bool) log sqls (sqlalchemy)
	"""
	log_fullpath = os.path.abspath(filename)
	log_dir = os.path.dirname(log_fullpath)
	log_dir_access = os.access(log_dir, os.W_OK)

	create_temp = False
	if os.path.isabs(filename):
		if not log_dir_access:
			create_temp = True
	else:
		if appconfig.is_frozen() or not log_dir_access:
			create_temp = True

	if create_temp:
		basename = os.path.basename(filename)
		spfname = os.path.splitext(basename)
		filename = spfname[0] + "_" + str(int(time.time())) + spfname[1]
		log_fullpath = os.path.join(tempfile.gettempdir(), filename)

	print 'Logging to %s' % log_fullpath

	if debug:
		level_console = logging.DEBUG
		level_file = logging.DEBUG
	else:
		level_console = logging.INFO
		level_file = logging.ERROR

	logging.basicConfig(level=level_file,
			format='%(asctime)s %(levelname)-8s %(name)s - %(message)s',
			filename=log_fullpath, filemode='w')
	console = logging.StreamHandler()
	console.setLevel(level_console)

	fmtr = logging.Formatter
	if sys.platform != 'win32':
		fmtr = ColorFormatter
	console.setFormatter(fmtr('%(levelname)-8s %(name)s - %(message)s'))
	logging.getLogger('').addHandler(console)

	logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO if debug_sql
			else logging.WARN)

	log = logging.getLogger(__name__)
	log.debug('logging_setup() finished')
