# -*- coding: utf-8 -*-
""" Various formatting function.

Copyright (c) Karol Będkowski, 2013

This file is part of wxGTD
Licence: GPLv2+
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2010-2013"
__version__ = "2013-05-05"

import time
import logging
import datetime

from wxgtd.lib import datetimeutils as DTU


_LOG = logging.getLogger(__name__)


def format_timestamp(timestamp, show_time=True, datetime_in_utc=True):
	""" Format date time object.

	Args:
		timestamp: date/time as str/unicode, datetime or number.
		show_time: if true also show time.
	"""
	if not timestamp:
		return ""
	if isinstance(timestamp, (str, unicode)):
		return timestamp
	if isinstance(timestamp, datetime.datetime):
		if datetime_in_utc:
			timestamp = DTU.datetime_utc2local(timestamp)
		if show_time:
			return timestamp.strftime("%x %X")
		return timestamp.strftime("%x")
	if show_time:
		return time.strftime("%x %X", time.localtime(timestamp))
	return time.strftime("%x", time.localtime(timestamp))
