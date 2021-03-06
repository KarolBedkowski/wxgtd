#!/usr/bin/python
# -*- coding: utf-8 -*-
""" Functions for synchronisation data between database and sync file.

Copyright (c) Karol Będkowski, 2013

This file is part of wxGTD
Licence: GPLv2+
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2013"
__version__ = '2013-04-26'

import logging
import gettext
import os
import datetime

from wxgtd.wxtools.wxpub import publisher

from wxgtd.lib import appconfig

from wxgtd.model import exporter
from wxgtd.model import loader


_LOG = logging.getLogger(__name__)
_ = gettext.gettext


class SyncLockedError(RuntimeError):
	""" Sync folder is locked. """
	pass


class OtherSyncError(RuntimeError):
	""" Other (unknown) syncing error. """
	pass


def _notify_progress(progress, msg):
	publisher.sendMessage('sync.progress',
			data=(progress, msg))


def sync(filename, load_only=False, notify_cb=_notify_progress):
	""" Sync data from/to given file.

	Notify progress by publisher.

	Args:
		filename: full path to file
		load_only: only load, not write data

	Raises:
		SyncLockedError when source file is locked.
	"""
	_LOG.info("sync: %r", filename)
	notify_cb(0, _("Sync via file %s") % filename)
	notify_cb(0, _("Creating backup"))
	create_backup()
	notify_cb(25, _("Sanity check"))
	_sync_file_check(filename)
	notify_cb(50, _("Checking sync lock"))
	if exporter.create_sync_lock(filename):
		notify_cb(1, _("Loading..."))
		try:
			if loader.load_from_file(filename, notify_cb):
				if not load_only:
					exporter.save_to_file(filename, notify_cb)
		except Exception as err:
			_LOG.exception("file sync error")
			raise OtherSyncError(err)
		finally:
			notify_cb(50, _("Removing sync lock"))
			exporter.delete_sync_lock(filename)
		notify_cb(100, _("Completed"))
	else:
		notify_cb(100, _("Synchronization file is locked. "
			"Can't synchronize..."))
		raise SyncLockedError()


def create_backup():
	""" Create backup current data in database.

	Format of backup file is identical with synchronization file.
	Backup are stored for default in ~/.local/share/wxgtd/backups/

	Configuration in wxgtd.conf:
	[backup]
	number_copies = 21
	location = <path to dir>
	"""
	appcfg = appconfig.AppConfig()
	backup_dir = appcfg.get('backup', 'location')
	if backup_dir:
		backup_dir = os.path.expanduser(backup_dir)
	else:
		backup_dir = os.path.join(appcfg.user_share_dir, 'backups')
	filename = os.path.join(backup_dir,
			"BACKUP_" + datetime.date.today().isoformat() + ".json.zip")
	_LOG.info('create_backup: %s', filename)
	if os.path.isfile(filename):
		_LOG.info("create_backup: today backup already exists; skipping...")
		return True
	if os.path.isdir(backup_dir):
		num_files_to_keep = int(appcfg.get('backup', 'number_copies', 21))
		# backup dir exists; check number of files and delete if more than 21
		files = sorted((fname for fname in os.listdir(backup_dir)
				if fname.startswith('BACKUP') and fname.endswith('.json.zip')),
				reverse=True)
		if len(files) >= num_files_to_keep:
			for fname in files[num_files_to_keep:]:
				_LOG.info('create_backup: delete backup: %r', fname)
				os.unlink(os.path.join(backup_dir, fname))
	else:
		try:
			os.mkdir(backup_dir)
		except IOError as error:
			_LOG.error('create_backup: create dir error: %s', str(error))
			return False
	# backup is regular export (zip)
	exporter.save_to_file(os.path.join(backup_dir, filename),
			internal_fname="GDT_SYNC.json")
	_LOG.info('create_backup: COMPLETED %s', filename)
	return True


def _sync_file_check(filename):
	directory = os.path.dirname(filename)
	if not os.path.isdir(directory):
		raise OtherSyncError(_("Sync directory not exists."))
	files = os.listdir(directory)
	if 'sync.locked' in files:
		files.remove('sync.locked')
	if len(files) > 2:
		raise OtherSyncError(_("To many files in sync directory."))
