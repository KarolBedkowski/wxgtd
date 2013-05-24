# -*- coding: utf-8 -*-
""" Splash screen window.

Copyright (c) Karol Będkowski, 2013

This file is part of wxGTD
Licence: GPLv2+
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2010-2013"
__version__ = "2013-04-28"


import wx

from wxgtd import version
from wxgtd.lib.appconfig import AppConfig


class Splash(wx.SplashScreen):
	""" Splash Screen class. """

	def __init__(self):
		config = AppConfig()
		splash_img = wx.Image(config.get_data_file('splash.png'))
		wx.SplashScreen.__init__(self, splash_img.ConvertToBitmap(),
			wx.SPLASH_CENTRE_ON_SCREEN | wx.SPLASH_TIMEOUT,
			2000, None, -1)

		wnd = self.GetSplashWindow()
		ver = wx.StaticText(wnd, -1, version.VERSION, pos=(330, 170))
		ver.SetBackgroundColour(wx.WHITE)
		wnd.Update()
