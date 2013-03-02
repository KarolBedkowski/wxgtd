#!/usr/bin/python
# -*- coding: utf-8 -*-
# pylint: disable-msg=R0901, R0904
"""
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2009-2013"
__version__ = "2010-10-13"

__all__ = ['show_about_box']


import wx

from wxgtd import version


def show_about_box(_parent):
	info = wx.AboutDialogInfo()
	info.SetName(version.NAME)
	info.SetVersion(version.VERSION)
	info.SetCopyright(version.COPYRIGHT)
	info.SetDevelopers(version.DEVELOPERS.splitlines())
	info.SetTranslators(version.TRANSLATORS.splitlines())
	info.SetLicense(version.LICENSE)
	info.SetDescription(version.DESCRIPTION + "\n" + version.RELEASE)
	wx.AboutBox(info)
