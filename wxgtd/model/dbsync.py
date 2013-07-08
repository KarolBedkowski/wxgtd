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


import os
import logging
import gettext
import tempfile
import datetime

try:
	import cjson
	_JSON_DECODER = cjson.decode
	_JSON_ENCODER = cjson.encode
except ImportError:
	import json
	_JSON_DECODER = json.loads
	_JSON_ENCODER = json.dumps

try:
	import dropbox
except ImportError:
	dropbox = None  # pylint: disable=C0103

try:
	from wx.lib.pubsub.pub import Publisher
except ImportError:
	from wx.lib.pubsub import Publisher  # pylint: disable=E0611

from wxgtd.lib import appconfig

from wxgtd.model import exporter
from wxgtd.model import loader
from wxgtd.model import sync as SYNC
from wxgtd.model import objects


_LOG = logging.getLogger(__name__)
_ = gettext.gettext


DEST = '/Apps/DGT-GTD/sync/GTD_SYNC.zip'
LOCK_FILENAME = '/Apps/DGT-GTD/sync/sync.locked'


def is_available():
	return bool(dropbox)


def _notify_progress(progress, msg):
	Publisher().sendMessage('sync.progress',
			data=(progress, msg))


def _create_session():
	appcfg = appconfig.AppConfig()
	sess = dropbox.session.DropboxSession(appcfg.get('dropbox', 'appkey'),
			appcfg.get('dropbox', 'appsecret'), 'dropbox')
	sess.set_token(appcfg.get('dropbox', 'oauth_key'),
			appcfg.get('dropbox', 'oauth_secret'))
	return dropbox.client.DropboxClient(sess)


def download_file(fileobj, source, dbclient):
	_LOG.info('download_file')
	try:
		remote_file, metadata = dbclient.get_file_and_metadata(source)
		if metadata and metadata['bytes'] > 0:
			fileobj.write(remote_file.read())
			return True
	except dropbox.rest.ErrorResponse:
		_LOG.warn("download_file: %r not found", source)
	return False


def sync(load_only=False, notify_cb=_notify_progress):
	""" Sync data from/to given file.

	Notify progress by Publisher().

	Args:
		load_only: only load, not write data

	Raises:
		SyncLockedError when source file is locked.
	"""
	_LOG.info("sync: %r", DEST)
	if not dropbox:
		raise SYNC.OtherSyncError(_("Dropbox is not available."))
	if not appconfig.AppConfig().get('dropbox', 'oauth_secret'):
		raise SYNC.OtherSyncError(_("Dropbox is not configured."))
	notify_cb(0, _("Sync via Dropbox API...."))
	notify_cb(1, _("Creating backup"))
	SYNC.create_backup()
	notify_cb(25, _("Checking sync lock"))
	try:
		dbclient = _create_session()
	except dropbox.rest.ErrorResponse as error:
		raise SYNC.OtherSyncError(_("Dropbox: connection failed: %s") %
				str(error))
	temp_file = tempfile.NamedTemporaryFile(suffix='.zip', delete=False)
	temp_filename = temp_file.name
	if create_sync_lock(dbclient):
		notify_cb(2, _("Downloading..."))
		try:
			loaded = download_file(temp_file, DEST, dbclient)
			temp_file.close()
			if loaded:
				loader.load_from_file(temp_filename, notify_cb)
			if not load_only:
				exporter.save_to_file(temp_filename, notify_cb, 'GTD_SYNC.json')
				try:
					dbclient.file_delete(DEST)
				except dropbox.rest.ErrorResponse:
					pass
				notify_cb(20, _("Uploading..."))
				with open(temp_filename) as temp_file:
					dbclient.put_file(DEST, temp_file)
		except Exception as err:
			_LOG.exception("file sync error")
			raise SYNC.OtherSyncError(err)
		finally:
			notify_cb(90, _("Removing sync lock"))
			try:
				dbclient.file_delete(LOCK_FILENAME)
			except dropbox.rest.ErrorResponse:
				_LOG.exception('create_sync_lock get lock')
			try:
				os.unlink(temp_filename)
			except IOError:
				pass
		notify_cb(100, _("Completed"))
	else:
		notify_cb(100, _("Synchronization file is locked. "
			"Can't synchronize..."))
		raise SYNC.SyncLockedError()


def create_sync_lock(dbclient):
	""" Check if lockfile exists in sync folder. Create if not.

	Args:
		dbclient: dropbox client session

	Returns:
		False, if directory is locked.
	"""
	try:
		data = dbclient.metadata(LOCK_FILENAME)
		if data and data['bytes'] > 0:
			return False
	except dropbox.rest.ErrorResponse:
		_LOG.exception('create_sync_lock get lock')

	session = objects.Session()
	device_id = session.query(objects.Conf).filter_by(  # pylint: disable=E1101
			key='deviceId').first()
	synclog = {'deviceId': device_id.val,
			"startTime": fmt_date(datetime.datetime.utcnow())}
	session.flush()  # pylint: disable=E1101
	dbclient.put_file(LOCK_FILENAME, _JSON_ENCODER(synclog))
	return True


def fmt_date(date):
	""" Format date to format required by GTD.

	Args:
		date: date & time as datetime.datetime object

	Returns:
		formatted date or empty string when date is None
	"""
	if not date:
		return ""
	return date.strftime("%Y-%m-%dT%H:%M:%S.") + date.strftime("%f")[:3] + 'Z'
