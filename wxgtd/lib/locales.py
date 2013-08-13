# -*- coding: utf-8 -*-

""" Locale support functions.

Copyright (c) Karol Będkowski, 2013

This file is part of wxGTD
Licence: GPLv2+
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2013"
__version__ = "2013-06-26"


import os
import locale
import logging
import gettext


_LOG = logging.getLogger(__name__)


def setup_locale(app_config):
	""" setup locales and gettext """
	locales_dir = app_config.locales_dir
	package_name = 'wxgtd'
	_LOG.info('run: locale dir: %s', locales_dir)
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
	_LOG.info('locale: %s', str(locale.getlocale()))
