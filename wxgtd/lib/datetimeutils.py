#!/usr/bin/python
# -*- coding: utf-8 -*-
""" Date & Time utilities.

Copyright (c) Karol Będkowski, 2006-2013

This file is part of wxGTD

This is free software; you can redistribute it and/or modify it under the
terms of the GNU General Public License as published by the Free Software
Foundation, version 2.

"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2013"
__version__ = "2013-05-12"


import time
import datetime

from dateutil import tz

TZ_UTC = tz.tzutc()
TZ_LOCAL = tz.tzlocal()


def datetime_utc2local(date_time):
	""" Convert datetime object from UTC to local timezone. """
	return date_time.replace(tzinfo=TZ_UTC).astimezone(TZ_LOCAL)


def datetime_local2utc(date_time):
	""" Convert datetime object from local to UTC timezone. """
	return date_time.replace(tzinfo=TZ_LOCAL).astimezone(TZ_UTC).replace(
			tzinfo=None)


def datetime2timestamp(date_time, utc2local=True):
	""" Convert datetime object to timestamp.

	Args:
		date_time: object to convert
		utc2local: if True - convert time to local timezone.
	Return:
		timestamp - number
	"""
	if utc2local:
		date_time = datetime_utc2local(date_time)
	return time.mktime(date_time.timetuple())


def timestamp2datetime(timestamp, local2utc=True):
	""" Convert datetime object to timestamp.

	Args:
		timestamp: object to convert
		local2utc: if True - convert time to UTC timezone.
	Return:
		Date & time as datetime object.
	"""
	date_time = datetime.datetime.fromtimestamp(timestamp)
	if local2utc:
		date_time = datetime_local2utc(date_time)
	return date_time
