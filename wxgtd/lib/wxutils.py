#!/usr/bin/python
# -*- coding: utf-8 -*-

""" wx utlities
Copyright (c) Karol Będkowski, 2013

This file is part of wxGTD
Licence: GPLv2+
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2013"
__version__ = "2013-04-27"


from contextlib import contextmanager
from functools import wraps

import wx


@contextmanager
def with_wait_cursor():
	""" Set "HOURGLASS_CURSOR" when executing part of code. """
	wx.SetCursor(wx.HOURGLASS_CURSOR)
	try:
		yield
	finally:
		wx.SetCursor(wx.STANDARD_CURSOR)


def call_after(func):
	""" Call decorated function with wxCallAfter. """
	@wraps(func)
	def wrapper(*args, **kwds):
		wx.CallAfter(func, *args, **kwds)
	return wrapper


@contextmanager
def with_freeze(*windows):
	""" Set freeze on window when executing closure. """
	for win in windows:
		win.Freeze()
	try:
		yield
	finally:
		for win in windows:
			win.Thaw()
