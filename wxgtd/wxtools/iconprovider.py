#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
## pylint: disable-msg=W0401, C0103
"""Images provider.

Copyright (c) Karol Będkowski, 2007-2013

This file is part of kPyLibs

This is free software; you can redistribute it and/or modify it under the
terms of the GNU General Public License as published by the Free Software
Foundation, version 2.
"""

__author__ = 'Karol Będkowski'
__copyright__ = 'Copyright (c) Karol Będkowski 2007-2013'
__version__ = '2013-04-27'


import logging
import os.path

import wx

from wxgtd.lib.singleton import Singleton


_LOG = logging.getLogger(__name__)
# supported image formats
_FILE_TYPES = (
		(wx.BITMAP_TYPE_PNG, '.png'),
		(wx.BITMAP_TYPE_ICO, '.ico'),
		(wx.BITMAP_TYPE_JPEG, '.jpg'),
)


class _IconProviderCache(Singleton):
	""" Images cache.

	Args:
		icons_pkg: python module/package that contains encoded icons
		icons_directory: directory containing images.
	"""

	def _init(self, icons_pkg=None, icons_directory=None):
		self._icons_cache = {}
		self._icons_pkg = icons_pkg
		self._icons_dir = icons_directory
		if not icons_pkg and not icons_directory:
			_LOG.error("_IconProviderCache: no icons_directory and icons_pkg!")
		if icons_directory and not os.path.isdir(icons_directory):
			_LOG.error("_IconProviderCache: can't find icons_directory %r",
					icons_directory)

	def _load_image(self, name):
		""" Get icon with given name.

		If image is cached - return it from cache. Otherwise load and add to
		cache. Also load icons from standard wxArtProvider by given id.

		Args:
			name: icon name without extension.
		Return:
			wxBitmap object.
		"""
		# load from wxArtProvider
		bitmap = wx.ArtProvider_GetBitmap(name)
		if not bitmap and not bitmap.IsNull():
			return bitmap
		bitmap = None
		# load from directory
		if self._icons_dir:
			bitmap = self._try_to_load_from_dir(name)
		# load from package
		if bitmap is None and self._icons_pkg is not None:
			attrname = 'get_%s_Image' % name
			if hasattr(self._icons_pkg, attrname):
				bitmap = getattr(self._icons_pkg, attrname)()
		if bitmap is None:
			_LOG.warn('_IconProviderCache._load_image(%s): not found' % name)
			return wx.NullBitmap
		self._icons_cache[name] = bitmap
		return bitmap

	def __getitem__(self, name):
		icon = self._icons_cache.get(name)
		if not icon:
			icon = self._load_image(name)
		return icon

	def __contains__(self, key):
		return key in self._icons_cache

	def _try_to_load_from_dir(self, name):
		""" Try to find & load icon with given name from data directory.

		Args:
			name: image without extension
		Returns:
			wxBitmap or None if icon not found
		"""
		for img_type, img_ext in _FILE_TYPES:
			filename = os.path.join(self._icons_dir, name + img_ext)
			if not os.path.isfile(filename):
				continue
			bitmap = None
			try:
				bitmap = wx.Bitmap(filename, img_type)
			except IOError, err:
				_LOG.debug('_IconProviderCache._try_to_load_from_dir(%s): %s',
						name, str(err))
			else:
				if bitmap and not bitmap.IsNull():
					return bitmap
		return None


class IconProvider:
	""" Wrapper for wxImageList with dynamic loading images.

	Contains wxBitmap objects for controls like wxListCtrl.

	Args:
		image_size: size images in wxImageList.
	"""

	def __init__(self, image_size=16):
		self._image_list = wx.ImageList(image_size, image_size)
		self._image_mapping = {}

	@property
	def image_list(self):
		""" Return wxImageList object """
		return self._image_list

	def load_icons(self, names):
		""" Load icons into list.

		Args:
			names: list of image names without extension.
		"""
		for name in names:
			if name in self._image_mapping:
				continue
			# try to load
			image = get_image(name)
			if image is None:
				_LOG.warn('load icon %s failed', name)
				continue
			# add image to wxImageList
			if isinstance(image, wx.Icon):
				self._image_mapping[name] = self._image_list.AddIcon(image)
			elif isinstance(image, wx.Bitmap):
				self._image_mapping[name] = self._image_list.Add(image)
			else:
				self._image_mapping[name] = self._image_list.Add(
						image.ConvertToBitmap())

	def get_image_index(self, name):
		""" Get index image in wxImageList.

		Args:
			name: image name
		Returns:
			index (number).
		"""
		return self._image_mapping.get(name)


def init_icon_cache(icons_package, data_dir):
	""" Init icon cache.

	Args:
		icons_package: python package contains encoded images (optional)
		data_dir: directory with images.
	"""
	_IconProviderCache(icons_package, data_dir)


def get_icon(name):
	""" Load & return wxIcon object with given name.

	Args:
		name: image name or wxArtProvider id.
	Returns:
		wxIcon object or None
	"""
	image = get_image(name)
	icon = None
	if isinstance(image, wx.Icon):
		icon = image
	elif image is not None:
		if isinstance(image, wx.Image):
			image = image.ConvertToBitmap()
		icon = wx.EmptyIcon()
		icon.CopyFromBitmap(image)
	return icon


def get_image(name):
	""" Load & return wxBitmap object with given name.

	Args:
		name: image name or wxArtProvider id.
	Returns:
		wxBitmap object or None
	"""
	return _IconProviderCache()[name]
