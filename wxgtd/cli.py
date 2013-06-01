# -*- coding: utf-8 -*-
""" Main module - cli interface

Copyright (c) Karol Będkowski, 2013

This file is part of wxGTD
Licence: GPLv2+
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2013"
__version__ = "2013-06-01"


import os
import gettext
import locale
import optparse
import logging

import sys
reload(sys)
try:
	sys.setappdefaultencoding("utf-8")  # pylint: disable=E1101
except AttributeError:
	sys.setdefaultencoding("utf-8")  # pylint: disable=E1101


_LOG = logging.getLogger(__name__)


from wxgtd import version


def _parse_opt():
	""" Parse cli options. """
	optp = optparse.OptionParser(version=version.NAME + " " + version.VERSION)
	group = optparse.OptionGroup(optp, "Creating tasks")
	group.add_option('--quick-task', '-q', dest="quick_task_title",
			help='add quickly task', type="string")
#	group.add_option('--hotlist', action="store_true",
#			dest="hotlist", help='show task in hotlist')
	optp.add_option_group(group)
	group = optparse.OptionGroup(optp, "Debug options")
	group.add_option('--debug', '-d', action="store_true", default=False,
			help='enable debug messages')
	group.add_option('--debug-sql', action="store_true", default=False,
			help='enable sql debug messages')
	optp.add_option_group(group)
	options, args = optp.parse_args()
	if not options.quick_task_title:
		optp.print_help()
		exit(0)
	return options, args


def _setup_locale(app_config):
	""" setup locales and gettext """
	locales_dir = app_config.locales_dir
	package_name = 'wxgtd'
	_LOG.info('run: locale dir: %s' % locales_dir)
	try:
		locale.bindtextdomain(package_name, locales_dir)
		locale.bind_textdomain_codeset(package_name, "UTF-8")
	except AttributeError:
		pass
	default_locale = locale.getdefaultlocale()
	locale.setlocale(locale.LC_ALL, '')
	os.environ['LC_ALL'] = os.environ.get('LC_ALL') or default_locale[0]
	gettext.install(package_name, localedir=locales_dir, unicode=True,
			names=("ngettext", ))
	gettext.bindtextdomain(package_name, locales_dir)
	gettext.textdomain(package_name)
	gettext.bindtextdomain('wxstd', locales_dir)
	gettext.bind_textdomain_codeset(package_name, "UTF-8")
	_LOG.info('locale: %s' % str(locale.getlocale()))


def _try_path(path):
	""" Check if in given path exists wxgtd.db file. """
	file_path = os.path.join(path, 'wxgtd.db')
	if os.path.isfile(file_path):
		return file_path
	return None


def _create_file_dir(db_filename):
	""" Create dirs for given file if not exists. """
	db_dirname = os.path.dirname(db_filename)
	if not os.path.isdir(db_dirname):
		os.mkdir(db_dirname)


def _find_db_file(config):
	""" Find existing database file. """
	db_filename = _try_path(config.main_dir)
	if not db_filename:
		db_filename = _try_path(os.path.join(config.main_dir, 'db'))
	if not db_filename:
		db_dir = os.path.join(config.main_dir, 'db')
		if os.path.isdir(db_dir):
			db_filename = os.path.join(db_dir, 'wxgtd.db')
	if not db_filename:
		db_filename = os.path.join(config.user_share_dir, 'wxgtd.db')
	return db_filename


def run():
	""" Run application. """
	# parse options
	options, args = _parse_opt()

	# app config
	from wxgtd.lib import appconfig

	# logowanie
	from wxgtd.lib.logging_setup import logging_setup
	logging_setup('wxgtd.log', options.debug, options.debug_sql)

	# konfiguracja
	config = appconfig.AppConfig('wxgtd.cfg', 'wxgtd')
	config.load_defaults(config.get_data_file('defaults.cfg'))
	config.load()
	config.debug = options.debug

	# locale
	_setup_locale(config)

	# database
	from wxgtd.model import db
	db_filename = _find_db_file(config)
	_create_file_dir(db_filename)
	# connect to databse
	db.connect(db_filename, options.debug_sql)

	if options.quick_task_title:
		from wxgtd.logic import quicktask as quicktask_logic
		quicktask_logic.create_quicktask(options.quick_task_title)
		config.save()
	exit(0)
