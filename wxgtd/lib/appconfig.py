# -*- coding: utf-8 -*-
# pylint: disable-msg=C0103
""" Application configuration.

Copyright (c) Karol Będkowski, 2007-2014

This file is part of kPyLibs

This is free software; you can redistribute it and/or modify it under the
terms of the GNU General Public License as published by the Free Software
Foundation, version 2.
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2013"
__version__ = "2011-04-24"

import sys
import os
import imp
import logging
import ConfigParser
import base64
import binascii

from wxgtd import configuration
from wxgtd.lib.singleton import Singleton

_LOG = logging.getLogger(__name__)


class AppConfig(Singleton):
	""" Object holding, loading and saving configuration.

	Args:
		filename: path for configuration file
		app_name: name of applicaiton
		main_dir: directory containing main file
	"""
	# pylint: disable=R0902

	def _init(self, filename, app_name, main_dir=None):
		# pylint: disable=W0221
		_LOG.debug('AppConfig.__init__(%r, %r, %r)', filename, app_name,
				main_dir)
		self._user_home = os.path.expanduser('~')
		self.app_name = app_name
		self.main_is_frozen = is_frozen()
		self.main_dir = main_dir or self._get_main_dir()
		self.config_path = self._get_config_path(app_name)
		self.data_dir = self._get_data_dir()
		self._filename = os.path.join(self.config_path, filename)
		self._config = ConfigParser.SafeConfigParser()
		self.clear()
		_LOG.debug('AppConfig.__init__: frozen=%(main_is_frozen)r, '
				'main_dir=%(main_dir)s, config=%(_filename)s, '
				'data=%(data_dir)s', self.__dict__)

	###########################################################################

	def __len__(self):
		return len(self._config.sections())

	def _get_debug(self):
		return self._runtime_params.get('DEBUG', False)

	def _set_debug(self, value):
		self._runtime_params['DEBUG'] = value

	debug = property(_get_debug, _set_debug)

	def r_set(self, key, value):
		self._runtime_params[key] = value

	def r_get(self, key, default=None):
		self._runtime_params.get(key, default)

	###########################################################################

	@property
	def locales_dir(self):
		""" Find directory with localisation files. """
		if self.main_is_frozen:
			if not sys.platform.startswith('win32'):
				return os.path.join(sys.prefix, configuration.LINUX_LOCALES_DIR)
		return os.path.join(self.main_dir, configuration.LOCALES_DIR)

	@property
	def user_share_dir(self):
		""" Get path to app local/share directory.

		Default: ~/.local/share/<app_name>/
		"""
		return os.path.join(self._user_home, '.local', 'share', self.app_name)

	def clear(self):
		""" Clear all data in object. """
		self.last_open_files = []
		for section in self._config.sections():
			self._config.remove_section(section)
		self._runtime_params = {}

	def load(self):
		""" Load application configuration file. """
		if self.load_configuration_file(self._filename):
			self._after_load(self._config)

	def load_defaults(self, filename):
		""" Load default configuration file. """
		if filename:
			self.load_configuration_file(filename)

	def load_configuration_file(self, filename):
		""" Load configuration file. """
		if not os.path.exists(filename):
			_LOG.warn("AppConfig.load_configuration_file: file %r not found",
					filename)
			return False
		_LOG.info('AppConfig.load_configuration_file: %r', filename)
		try:
			with open(filename, 'r') as cfile:
				self._config.readfp(cfile)
		except StandardError:
			_LOG.exception('AppConfig.load_configuration_file error')
			return False
		_LOG.debug('AppConfig.load_configuration_file finished')
		return True

	def save(self):
		""" Save configuration. """
		_LOG.debug('AppConfig.save')
		self._before_save(self._config)
		try:
			with open(self._filename, 'w') as cfile:
				self._config.write(cfile)
		except StandardError:
			_LOG.exception('AppConfig.save error')
		_LOG.debug('AppConfig.save finished')

	def add_last_open_file(self, filename):
		""" Put filename into last files list.

		Given filename is appended (moved if exists) on the beginning.
		"""
		if filename in self.last_open_files:
			self.last_open_files.remove(filename)
		self.last_open_files.insert(0, filename)
		self.last_open_files = self.last_open_files[:7]

	def get_data_file(self, filename):
		""" Get full path to file in data directory.

		Args:
			filename: file name to find

		Returns:
			Full path or None if file not exists.
		"""
		path = os.path.join(self.data_dir, filename)
		if os.path.exists(path):
			return path
		_LOG.warn('AppConfig.get_data_file(%s) not found', filename)
		return None

	def get(self, section, key, default=None):
		""" Get value from configuration.

		Args:
			section: section of configuration (string)
			key: key name (string)
			default: optional default value (default=None)
		"""
		if (self._config.has_section(section)
				and self._config.has_option(section, key)):
			try:
				return eval(self._config.get(section, key))
			except:  # catch all errors; pylint: disable=W0702
				_LOG.exception('AppConfig.get(%s, %s, %r)', section, key, default)
		return default

	def get_items(self, section):
		""" Get all key-value pairs in given config section.

		Args:
			section: section name (string)

		Return:
			List of (key, value) or None if section not found.
		"""
		if self._config.has_section(section):
			try:
				items = self._config.items(section)
				if items:
					result = list((key, eval(val)) for key, val in items)
				return result
			except:  # catch all errors; pylint: disable=W0702
				_LOG.exception('AppConfig.get(%s)', section)
		return None

	def get_secure(self, section, key, default=None):
		""" Get "secure" stored value.

		Args:
			section: section of configuration (string)
			key: key name (string)
			default: optional default value (default=None)
		"""
		value = self.get(section, key, default)
		try:
			value = base64.decodestring(value)
		except binascii.Error:
			_LOG.warn('AppConfig.get_secure error for (%r, %r, %r), %r', section,
					key, default, value)
		return value

	def set(self, section, key, val):
		""" Store value in configuration.

		Create section if necessary.

		Args:
			section: section of configuration (string)
			key: key name (string)
			val:  value to store.
		"""
		if not self._config.has_section(section):
			self._config.add_section(section)
		self._config.set(section, key, repr(val))

	def set_items(self, section, key, items):
		""" Store values in configuration.

		Create section if necessary.
		Each item in items is stored as key+sequence number.

		Args:
			section: section of configuration (string)
			key: key name (string)
			items: values to store.
		"""
		config = self._config
		if config.has_section(section):
			config.remove_section(section)
		config.add_section(section)
		for idx, item in enumerate(items):
			config.set(section, '%s%05d' % (key, idx), repr(item))

	def set_secure(self, section, key, val):
		""" Store "secure" value in configuration.
		Args:
			section: section of configuration (string)
			key: key name (string)
			val: value to store.
		"""
		self.set(section, key, base64.encodestring(val))

	def _get_main_dir(self):
		""" Find main application directory. """
		if self.main_is_frozen:
			if sys.platform == 'win32':
				return os.path.abspath(os.path.dirname(sys.executable))
		return os.path.abspath(os.path.dirname(sys.argv[0]))

	def _get_config_path(self, app_name):
		""" Get path to config file. Create directories if not exists.

		Config is stored in ~/.config/<app_name>
		"""
		config_path = os.path.join(self._user_home, '.config', app_name)
		if not os.path.exists(config_path):
			try:
				os.makedirs(config_path)
			except IOError:
				_LOG.exception('Error creating config directory: %s',
						self.config_path)
				config_path = self.main_dir
		return config_path

	def _get_data_dir(self):
		""" Find path to directory with data files. """
		if self.main_is_frozen:
			if not sys.platform == 'win32':
				return os.path.join(sys.prefix, configuration.LINUX_DATA_DIR)
		return os.path.join(self.main_dir, configuration.DATA_DIR)

	def _after_load(self, config):
		""" Action to take after loaded configuration. """
		if config.has_section('last_files'):
			# load last files
			self.last_open_files = [val[1] for val in config.items('last_files')]

	def _before_save(self, config):
		""" Action to take before save configuration. """
		# store last files
		if config.has_section('last_files'):
			config.remove_section('last_files')
		config.add_section('last_files')
		last_open_files = self.last_open_files[:7]
		for fidn, fname in enumerate(last_open_files):
			config.set('last_files', 'file%d' % fidn, fname)


class AppConfigWrapper(object):
	""" Wrapper for AppConfig class that allow use it with validators.
	Values are accessible by <section>/<key>."""
	# pylint: disable=R0903

	def __init__(self):
		self._config = AppConfig()

	def __getitem__(self, key):
		key = key.split('/')
		value = self._config.get(key[0], key[1])
		_LOG.debug("AppConfigWrapper.get(%r) -> %r", key, value)
		return value

	def __setitem__(self, key, value):
		key = key.split('/')
		self._config.set(key[0], key[1], value)

	def __delitem__(self, _key):
		pass

	def __len__(self):
		return len(self._config)

	def get(self, key, default=None):
		key = key.split('/')
		return self._config.get(key[0], key[1], default)


def is_frozen():
	""" Check if application is frozen. """
	if __file__.startswith(sys.prefix):
		return True
	return (hasattr(sys, "frozen")		# new py2exe
			or hasattr(sys, "importers")		# old py2exe
			or imp.is_frozen("__main__"))		# tools/freeze


if __name__ == '__main__':
	acfg = AppConfig('test.cfg')
	acfg.last_open_files = ['1', '2', 'q', 'w']
	print id(acfg), acfg.last_open_files
	acfg.save()

	acfg.clear()
	print id(acfg), acfg.last_open_files

	acfg = AppConfig('test.cfg')
	acfg.load()
	print id(acfg), acfg.last_open_files
