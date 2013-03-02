#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
# pylint: disable-msg=R0901, R0904
"""
Shell

KPyLibs
Copyright (c) Karol Będkowski, 2004, 2005, 2006

This file is part of KPyLibs
"""

__author__ = 'Karol Będkowski'
__copyright__ = 'Copyright (C) Karol Będkowski 2006'
__revision__ = '$Id$'
__all__ = ['WndShell']


import logging

import wx
import wx.py


_LOG = logging.getLogger(__name__)


class WndShell(wx.Frame):
	''' Okno shella '''

	def __init__(self, parent, locals_vars):
		wx.Frame.__init__(self, parent, -1, 'Shell', size=(700, 500))
		wx.py.crust.Crust(self, locals=locals_vars)
		self.Centre(wx.BOTH)
		_LOG.debug('WndShell.__init__()')
