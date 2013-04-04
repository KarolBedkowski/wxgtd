# -*- coding: utf-8 -*-

"""
Formatery
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2010-2013"
__version__ = "2010-11-25"

import time
import logging
import datetime

_LOG = logging.getLogger(__name__)


def format_timestamp(timestamp, show_time):
	if not timestamp:
		return ""
	if isinstance(timestamp, (str, unicode)):
		return timestamp
	if isinstance(timestamp, datetime.datetime):
		if show_time:
			return timestamp.strftime("%x %X")
		return timestamp.strftime("%x")
	if show_time:
		return time.strftime("%x %X", time.localtime(timestamp))
	return time.strftime("%x", time.localtime(timestamp))
