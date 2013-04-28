#!/usr/bin/python
# -*- coding: utf-8 -*-
# pylint: disable-msg=R0901, R0904
""" About dialog.

Copyright (c) Karol Będkowski, 2009-2013

This file is part of wxGTD
Licence: GPLv2+
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2009-2013"
__version__ = "2013-04-28"
__all__ = ['show_about_box']


import wx

from wxgtd import version


def show_about_box(_parent):
	""" Create and show about dialog. """
	info = wx.AboutDialogInfo()
	info.SetName(version.NAME)
	info.SetVersion(version.VERSION)
	info.SetCopyright(version.COPYRIGHT)
	info.SetDevelopers(version.DEVELOPERS.splitlines())
	info.SetTranslators(version.TRANSLATORS.splitlines())
	info.SetLicense(version.LICENSE)
	info.SetDescription(version.DESCRIPTION + "\n" + version.RELEASE)
	wx.AboutBox(info)
