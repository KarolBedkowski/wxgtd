# -*- coding: utf-8 -*-
""" Main module - cli interface

Copyright (c) Karol Będkowski, 2013

This file is part of wxGTD
Licence: GPLv2+
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2013"
__version__ = "2013-06-01"


import gettext
import optparse
import logging

import sys
reload(sys)
try:
	sys.setappdefaultencoding("utf-8")  # pylint: disable=E1101
except AttributeError:
	sys.setdefaultencoding("utf-8")  # pylint: disable=E1101

_ = gettext.gettext
_LOG = logging.getLogger(__name__)


from wxgtd import version
from wxgtd.model import queries


def _parse_opt():
	""" Parse cli options. """
	optp = optparse.OptionParser(version=version.NAME + " (CLI) " +
			version.VERSION)

	group = optparse.OptionGroup(optp, "List tasks")
	group.add_option('--tasks', '-t', action="store_const",
			const=queries.QUERY_ALL_TASK,
			dest="query_group", help='show all tasks')
	group.add_option('--hotlist', action="store_const",
			const=queries.QUERY_HOTLIST,
			dest="query_group", help='show task in hotlist')
	group.add_option('--today', action="store_const",
			const=queries.QUERY_TODAY,
			dest="query_group", help='show task with due date today')
	group.add_option('--starred', action="store_const",
			const=queries.QUERY_STARRED,
			dest="query_group", help='show starred tasks')
	group.add_option('--basket', action="store_const",
			const=queries.QUERY_BASKET,
			dest="query_group", help='show tasks in basket')
	group.add_option('--finished', action="store_const",
			const=queries.QUERY_FINISHED,
			dest="query_group", help='show finished tasks')
	group.add_option('--projects', action="store_const",
			const=queries.QUERY_PROJECTS,
			dest="query_group", help='show projects')
	group.add_option('--checklists', action="store_const",
			const=queries.QUERY_CHECKLISTS,
			dest="query_group", help='show checklists')
	group.add_option('--future-alarms', action="store_const",
			const=queries.QUERY_FUTURE_ALARMS,
			dest="query_group", help='show task with alarms in future')
	group.add_option('--trash', action="store_const",
			const=queries.QUERY_TRASH,
			dest="query_group", help='show deleted tasks')
	optp.add_option_group(group)

	group = optparse.OptionGroup(optp, "Task operations")
	group.add_option('--quick-task', '-q', dest="quick_task_title",
			help='quickly add new task', type="string")
	optp.add_option_group(group)

	group = optparse.OptionGroup(optp, "List tasks options")
	group.add_option('--show-finished', action="store_true",
			dest="query_show_finished", help='show finished tasks')
	group.add_option('--show-subtask', action="store_true",
			dest="query_show_subtask", help='show subtasks')
	group.add_option('--dont-hide-until', action="store_true",
			dest="query_dont_hide_until", help="show hidden task")
	group.add_option('--parent', dest="parent_uuid",
			help='set parent UUID for query')
	group.add_option('--search', '-s', dest="search_text",
			help='search for title/note')
	group.add_option('--verbose', '-v', action="count",
			dest="verbose", help='show more information')
	group.add_option('--output-csv', action="store_true",
			dest="output_csv", help='show result as csv file')
	optp.add_option_group(group)

	group = optparse.OptionGroup(optp, "Options")
	group.add_option('--sync', action="store_true", dest="sync",
			help='sync data on startup and exit')
	optp.add_option_group(group)

	group = optparse.OptionGroup(optp, "Debug options")
	group.add_option('--debug', '-d', action="store_true", default=False,
			help='enable debug messages')
	group.add_option('--debug-sql', action="store_true", default=False,
			help='enable sql debug messages')
	group.add_option("--shell", action="store_true", default=False,
			help="start shell", dest="shell")
	optp.add_option_group(group)
	options, args = optp.parse_args()
	if not any((options.quick_task_title, options.query_group >= 0,
			options.sync, options.shell)):
		optp.print_help()
		exit(0)
	return options, args


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
	from wxgtd.lib import locales
	locales.setup_locale(config)

	# database
	from wxgtd.model import db
	db_filename = db.find_db_file(config)
	# connect to databse
	db.connect(db_filename, options.debug_sql)

	if options.sync:
		_sync(config, True)
	if options.quick_task_title:
		from wxgtd.logic import quicktask as quicktask_logic
		quicktask_logic.create_quicktask(options.quick_task_title)
	elif options.query_group >= 0:
		_list_tasks(options, args)
	if options.sync:
		_sync(config, False)
	if options.shell:
		_shell()
	config.save()
	exit(0)


def _list_tasks(options, _args):
	""" List tasks action. """
	from wxgtd.model import objects as OBJ
	group_id = options.query_group
	query_opt = 0
	if options.query_show_finished:
		query_opt |= queries.OPT_SHOW_FINISHED
	if options.query_show_subtask:
		query_opt |= queries.OPT_SHOW_SUBTASKS
	if not options.query_dont_hide_until:
		query_opt |= queries.OPT_HIDE_UNTIL
	params = queries.build_query_params(group_id, query_opt,
			options.parent_uuid, options.search_text or '')

	tasks = OBJ.Task.select_by_filters(params)
	if options.output_csv:
		_print_csv_tasks_list(tasks, options.verbose)
	else:
		_print_simple_tasks_list(tasks, options.verbose)


def _print_simple_tasks_list(tasks, verbose):
	""" Export task list to stdout in human-friendly format. """
	from wxgtd.model import exporter
	exporter.dump_tasks_to_text(tasks, verbose)


def _print_csv_tasks_list(tasks, verbose):
	""" Export task list to stdout in cvs format. """
	from wxgtd.model import exporter
	exporter.dump_tasks_to_csv(tasks, verbose)


def _log_sync_cb(progress, msg):
	print >> sys.stderr, msg


def _sync(config, load_only):
	last_sync_file = config.get('files', 'last_sync_file')
	if last_sync_file:
		from wxgtd.model import sync
		sync.sync(last_sync_file, load_only, notify_cb=_log_sync_cb)


def _shell():
	# starting interactive shell
	from IPython.terminal import ipapp
	app = ipapp.TerminalIPythonApp.instance()
	app.initialize(argv=[])
	app.start()
