#!/usr/bin/python
# -*- coding: utf-8 -*-
# pylint: disable-msg=R0901, R0904
""" wxShell (pyCrust)

Copyright (c) Karol Będkowski, 2004-2013

This file is part of kPyLibs

This is free software; you can redistribute it and/or modify it under the
terms of the GNU General Public License as published by the Free Software
Foundation, version 2.
"""

__author__ = 'Karol Będkowski'
__copyright__ = 'Copyright (C) Karol Będkowski 2006-2013'
__version__ = "2013-04-27"
__all__ = ['WndShell']


import wx
import wx.py


class WndShell(wx.Frame):
	""" Window with pyCrust.

	Args:
		parent: parent window
		locals_vars: local variables to set in pyCrust.
	"""

	def __init__(self, parent, locals_vars):
		wx.Frame.__init__(self, parent, -1, 'Shell', size=(700, 500))
		wx.py.crust.Crust(self, locals=locals_vars)
		self.Centre(wx.BOTH)
