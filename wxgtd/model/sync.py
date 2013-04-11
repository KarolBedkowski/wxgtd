#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
"""

import logging
import gettext

try:
	from wx.lib.pubsub.pub import Publisher
except ImportError:
	from wx.lib.pubsub import Publisher

import exporter
import loader

_LOG = logging.getLogger(__name__)
_ = gettext.gettext


class SyncLockedError(RuntimeError):
	""" Synchronizacja jest zablokowana """
	pass


def _notify_loading_progress(progress, msg):
	Publisher.sendMessage('sync.progress',
			data=(progress * 0.45 + 2, msg))


def _notify_exporting_progress(progress, msg):
	Publisher.sendMessage('sync.progress',
			data=(progress * 0.45 + 52, msg))


def _notify_progress(progress, msg):
	Publisher.sendMessage('sync.progress',
			data=(progress, msg))


def sync(filename):
	""" Synchronizacja danych z podanym plikiem """
	_LOG.info("sync: %r", filename)
	_notify_progress(1, _("Checking sync lock"))
	if exporter.create_sync_lock(filename):
		try:
			if loader.load_from_file(filename,
					_notify_loading_progress):
				exporter.save_to_file(filename,
						_notify_exporting_progress)
		except:
			_LOG.exception("file sync error")
			raise SyncLockedError()
		finally:
			_notify_progress(99, _("Removing sync lock"))
			exporter.delete_sync_lock(filename)
		_notify_progress(100, _("Completed"))
