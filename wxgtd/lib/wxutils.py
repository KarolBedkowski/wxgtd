#!/usr/bin/python
# -*- coding: utf-8 -*-

from contextlib import contextmanager
from functools import wraps

import wx


@contextmanager
def with_wait_cursor():
	wx.SetCursor(wx.HOURGLASS_CURSOR)
	try:
		yield
	finally:
		wx.SetCursor(wx.STANDARD_CURSOR)


def call_after(func):

	@wraps(func)
	def wrapper(*args, **kwds):
		wx.CallAfter(func, *args, **kwds)
	return wrapper


@contextmanager
def with_freeze(*windows):
	""" Wyłaczenie odświerzania okna """
	for win in windows:
		win.Freeze()
	try:
		yield
	finally:
		for win in windows:
			win.Thaw()
