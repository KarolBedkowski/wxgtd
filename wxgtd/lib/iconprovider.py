#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#### p##ylint#: disable-msg=W0401, C0103
"""
Icon provider for windows

Copyright (c) Karol Będkowski, 2007-2011

This file is part of kPyLibs
"""

__author__ = 'Karol Będkowski'
__copyright__ = 'Copyright (c) Karol Będkowski 2007-2010'


import logging
import os.path

import wx

from .singleton import Singleton


_LOG = logging.getLogger(__name__)
_FILE_TYPES = (
		(wx.BITMAP_TYPE_PNG, '.png'),
		(wx.BITMAP_TYPE_ICO, '.ico'),
		(wx.BITMAP_TYPE_JPEG, '.jpg'),
)


class _IconProviderCache(Singleton):
	''' cache ikon '''

	def _init(self, icons, icons_directory):
		self.__icon_cache = {}
		self.__icons = icons
		self.__icons_dir = icons_directory

	def __load_icon(self, name):
		''' Zaladowanie podanej grafiki do cache '''
		bitmap = wx.ArtProvider_GetBitmap(name)
		if bitmap.IsNull():
			bitmap = None
			if self.__icons_dir:
				bitmap = self._try_to_load_from_dir(name)
			if bitmap is None and self.__icons is not None:
				attrname = 'get_%s_Image' % name
				if hasattr(self.__icons, attrname):
					bitmap = getattr(self.__icons, attrname)()
			if bitmap is None:
				_LOG.warn('_IconProviderCache.__load_icon(%s): not found' % name)
				bitmap = wx.NullBitmap
			else:
				self.__icon_cache[name] = bitmap
		return bitmap

	def __getitem__(self, name):
		icon = self.__icon_cache.get(name)
		if not icon:
			icon = self.__load_icon(name)
		return icon

	def __contains__(self, key):
		return key in self.__icon_cache

	def _try_to_load_from_dir(self, name):
		for img_type, img_ext in _FILE_TYPES:
			filename = os.path.join(self.__icons_dir, name + img_ext)
			if not os.path.isfile(filename):
				continue
			bitmap = None
			try:
				bitmap = wx.Bitmap(filename, img_type)
			except IOError, err:
				_LOG.debug('_IconProviderCache._try_to_load_from_dir(%s): %s',
						name, str(err))
			else:
				if bitmap and bitmap.IsNull():
					bitmap = None
			if bitmap:
				return bitmap
		return None


class IconProvider:
	""" Klasa dostarczająca ikonki """

	def __init__(self, size=16):
		self.__image_list = wx.ImageList(size, size)
		self.__image_dict = {}

	@property
	def image_list(self):
		""" ip.image_list -> wxImageList -- pobranie listy ikon """
		return self.__image_list

	def load_icons(self, names):
		''' ip.load_icons(names list) -- zaladowanie listy ikon '''
		for name in names:
			if name in self.__image_dict:
				continue
			image = get_image(name)
			if image is None:
				_LOG.warn('load icon %s failed', name)
				continue
			if isinstance(image, wx.Icon):
				self.__image_dict[name] = self.__image_list.AddIcon(image)
			elif isinstance(image, wx.Bitmap):
				self.__image_dict[name] = self.__image_list.Add(image)
			else:
				self.__image_dict[name] = self.__image_list.Add(image.ConvertToBitmap())

	def get_image_index(self, name):
		''' ip.get_image_index(name) -> index -- pobranie indexu obrazka '''
		return self.__image_dict.get(name)


def init_icon_cache(icons, data_dir):
	_IconProviderCache(icons, data_dir)


def get_icon(name):
	''' ip.get_icon(name) -> icon -- pobranie ikonku '''
	image = get_image(name)
	if isinstance(image, wx.Icon):
		icon = image
	elif image is not None:
		if isinstance(image, wx.Image):
			image = image.ConvertToBitmap()
		icon = wx.EmptyIcon()
		icon.CopyFromBitmap(image)
	else:
		icon = None
	return icon


def get_image(name):
	''' ip.get_image(name) -> image -- pobranie obrazka '''
	try:
		image = wx.ArtProvider_GetBitmap(name)
		if not image or image.IsNull():
			image = _IconProviderCache()[name]
	except (KeyError, AttributeError):
		_LOG.exception('get_image(%s) error' % name)
		image = None
	return image
