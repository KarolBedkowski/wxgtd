# -*- coding: UTF-8 -*-
""" Singleton base class.

Copyright (c) Karol Będkowski, 2013

This file is part of wxGTD
Licence: GPLv2+
"""


class Singleton(object):
	""" Base class for singleton.

	Require do not use __init__ constructor - instead overwrite _init method.
	"""
	# pylint: disable=R0903

	def __new__(cls, *args, **kwarg):
		instance = cls.__dict__.get('__instance__')
		if instance is None:
			instance = object.__new__(cls)
			# call _init as constructor
			instance._init(*args, **kwarg)  # pylint: disable=W0212
			cls.__instance__ = instance
		return instance

	def _init(self, *args, **kwarg):
		""" Object constructor. """
		pass

	@classmethod
	def _force_del(cls):
		""" Force delete class instance. """
		del cls.__instance__
		cls.__instance__ = None
