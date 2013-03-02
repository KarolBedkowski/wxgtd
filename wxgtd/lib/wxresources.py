# -*- coding: utf-8 -*-

"""
"""
from __future__ import with_statement


__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2004-2011"
__version__ = "2011-02-01"


import re
import locale

from wx import xrc
from wx.lib import masked
from wx.lib import colourselect as csel

from .appconfig import AppConfig


def _localize(match_object):
	return ''.join((match_object.group(1), _(match_object.group(2)),
			match_object.group(3)))


_CACHE = {}


class NumCtrlXmlHandler(xrc.XmlResourceHandler):
	def __init__(self):
		xrc.XmlResourceHandler.__init__(self)
		self.AddWindowStyles()

	def CanHandle(self, node):
		return self.IsOfClass(node, "NumCtrl")

	def DoCreateResource(self):
		fractionWidth = int(self.GetParamValue('fractionWidth')) \
				if self.HasParam('fractionWidth') else 2
		integerWidth = int(self.GetParamValue('integerWidth')) \
				if self.HasParam('integerWidth') else 2
		ctrl = masked.NumCtrl(
				self.GetParentAsWindow(),
				self.GetID(),
				allowNegative=False,
				fractionWidth=fractionWidth,
				integerWidth=integerWidth,
				groupChar=' ',
				allowNone=True,
				decimalChar=locale.localeconv()['decimal_point'],)
		self.SetupWindow(ctrl)
		self.CreateChildren(ctrl)
		return ctrl


class TimeCtrlXmlHandler(xrc.XmlResourceHandler):
	def __init__(self):
		xrc.XmlResourceHandler.__init__(self)
		self.AddWindowStyles()

	def CanHandle(self, node):
		return self.IsOfClass(node, "TimeCtrl")

	def DoCreateResource(self):
		ctrl = masked.TimeCtrl(
				self.GetParentAsWindow(),
				self.GetID(),
				display_seconds=True,
				fmt24hr=True)
		self.SetupWindow(ctrl)
		self.CreateChildren(ctrl)
		return ctrl


class ColourSelectHandler(xrc.XmlResourceHandler):
	def __init__(self):
		xrc.XmlResourceHandler.__init__(self)
		self.AddWindowStyles()

	def CanHandle(self, node):
		return self.IsOfClass(node, "ColourSelect")

	def DoCreateResource(self):
		ctrl = csel.ColourSelect(
				self.GetParentAsWindow(),
				self.GetID(),
				size=self.GetSize())
		self.SetupWindow(ctrl)
		self.CreateChildren(ctrl)
		return ctrl


def load_xrc_resource(filename):
	xrcfile_path = AppConfig().get_data_file(filename)
	res = _CACHE.get(xrcfile_path)
	if res is None:
		with open(xrcfile_path) as xrc_file:
			data = xrc_file.read()
		data = data.decode('UTF-8')
		re_gettext = re.compile(r'(\<label\>)(.*?)(\<\/label\>)')
		data = re_gettext.sub(_localize, data)
		re_gettext = re.compile(r'(\<title\>)(.*?)(\<\/title\>)')
		data = re_gettext.sub(_localize, data)
		re_gettext = re.compile(r'(\<tooltip\>)(.*?)(\<\/tooltip\>)')
		data = re_gettext.sub(_localize, data)
		data = data.encode('UTF-8')

		res = xrc.EmptyXmlResource()
		res.InsertHandler(NumCtrlXmlHandler())
		res.InsertHandler(TimeCtrlXmlHandler())
		res.InsertHandler(ColourSelectHandler())
		res.LoadFromString(data)
		_CACHE[xrcfile_path] = res

	return res
