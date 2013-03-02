# -*- coding: UTF-8 -*-
"""
Copyright (c) Karol Będkowski, 2013

This file is part of wxgtd

wxgtd is free software; you can redistribute it and/or modify it under the
terms of the GNU General Public License as published by the Free Software
Foundation, version 2.
"""


class Enum(object):
	def __init__(self, *args, **kwarg):
		self._const = dict(zip(args, xrange(len(args))), **kwarg)
		self.__dict__.update(self._const)

	def __len__(self):
		return len(self._const)

	def __iter__(self):
		return self._const.itervalues()

	def get_value_name(self, value):
		for key, val in self._const.iteritems():
			if val == value:
				return key
		raise KeyError('Invalid value')
