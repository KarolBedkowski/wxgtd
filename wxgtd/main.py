# -*- coding: utf-8 -*-
""" Main module - gui interface

Copyright (c) Karol Będkowski, 2013

This file is part of wxGTD
Licence: GPLv2+
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2013"
__version__ = "2013-04-27"


import os
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
	optp = optparse.OptionParser(version=version.NAME + " (GUI) " +
			version.VERSION)
	group = optparse.OptionGroup(optp, "Creating tasks")
	group.add_option('--quick-task-dialog', action="store_true", default=False,
			help='enable debug messages', dest="quick_task_dialog")
	optp.add_option_group(group)
	group = optparse.OptionGroup(optp, "Debug options")
	group.add_option('--debug', '-d', action="store_true", default=False,
			help='enable debug messages')
	group.add_option('--debug-sql', action="store_true", default=False,
			help='enable sql debug messages')
	group.add_option('--wx-inspection', action="store_true", default=False)
	optp.add_option_group(group)
	group = optparse.OptionGroup(optp, "Other options")
	group.add_option('--force-start', action="store_true", default=False,
			help='Force start application even other instance is running.')
	optp.add_option_group(group)
	return optp.parse_args()[0]


def _run_ipcs(config):
	from wxgtd.wxtools import ipc
	ipcs = ipc.IPC(os.path.join(config.config_path, "wxgtd_lock"))
	if not ipcs.startup("gui.frame_main.raise"):
		_LOG.info("App is already running...")
		exit(0)
	return ipcs


def run():
	""" Run application. """
	# parse options
	options = _parse_opt()

	# logowanie
	from wxgtd.lib.logging_setup import logging_setup
	logging_setup('wxgtd.log', options.debug, options.debug_sql)

	# app config
	from wxgtd.lib import appconfig
	config = appconfig.AppConfig('wxgtd.cfg', 'wxgtd')
	config.load_defaults(config.get_data_file('defaults.cfg'))
	config.load()
	config.debug = options.debug

	# locale
	from wxgtd.lib import locales
	locales.setup_locale(config)

	# importowanie wx
	try:
		import wxversion
		try:
			wxversion.select('2.8')
		except wxversion.AlreadyImportedError:
			pass
	except ImportError, err:
		print 'No wxversion.... (%s)' % str(err)

	import wx

	ipcs = None
	if not options.force_start:
		ipcs = _run_ipcs(config)

	# create app
	app = wx.App(False)
	if wx.version().startswith('2'):
		wx.InitAllImageHandlers()

	# splash screen
	if not options.quick_task_dialog:
		from wxgtd.gui.splash import Splash
		Splash().Show()
		wx.Yield()

	if sys.platform == 'win32':
		wx.Locale.AddCatalogLookupPathPrefix(config.locales_dir)
		wx.Locale(wx.LANGUAGE_DEFAULT).AddCatalog('wxstd')

	# connect to databse
	from wxgtd.model import db
	db.connect(db.find_db_file(config), options.debug_sql)

	if options.quick_task_dialog:
		from wxgtd.gui import quicktask
		quicktask.quick_task(None)
	else:
		# init icons
		from wxgtd.wxtools import iconprovider
		iconprovider.init_icon_cache(None, config.data_dir)

		# show main window
		from wxgtd.gui.frame_main import FrameMain
		main_frame = FrameMain()
		app.SetTopWindow(main_frame.wnd)
		if not config.get('gui', 'hide_on_start'):
			main_frame.wnd.Show()

		# optionally show inspection tool
		if options.wx_inspection:
			import wx.lib.inspection
			wx.lib.inspection.InspectionTool().Show()

		app.MainLoop()

	# app closed; save config
	if ipcs:
		ipcs.shutdown()
	config.save()
