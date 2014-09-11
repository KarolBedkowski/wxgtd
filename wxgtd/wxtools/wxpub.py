#!/usr/bin/python
# -*- coding: utf-8 -*-
# pylint: disable-msg=R0901, R0904
""" wx pubsub Publisher wrapper to support various wx versions.

Copyright (c) Karol Będkowski, 2015

This file is part of wxGTD

This is free software; you can redistribute it and/or modify it under the
terms of the GNU General Public License as published by the Free Software
Foundation, version 2.
"""

__author__ = 'Karol Będkowski'
__copyright__ = 'Copyright (C) Karol Będkowski 2013'
__version__ = "2013-07-11"

import logging

_LOG = logging.getLogger(__name__)

publisher = None

from wx.lib.pubsub import setuparg1
assert setuparg1

try:
	from wx.lib.pubsub.pub import Publisher
	publisher = Publisher()
	_LOG.debug("Using wx.lib.pubsub.pub.Publisher")
except ImportError:
	try:
		from wx.lib.pubsub import Publisher  # pylint: disable=E0611
		publisher = Publisher()
		_LOG.debug("Using wx.lib.pubsub.Publisher")
	except ImportError:
		from wx.lib.pubsub import pub
		publisher = pub
		_LOG.debug("Using wx.lib.pubsub.pub")
