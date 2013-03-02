# -*- coding: UTF-8 -*-


class Singleton(object):

	def __new__(cls, *args, **kwarg):
		instance = cls.__dict__.get('__instance__')
		if instance is None:
			instance = object.__new__(cls)
			instance._init(*args, **kwarg)
			cls.__instance__ = instance
		return instance

	def _init(self, *args, **kwarg):
		pass

	@classmethod
	def _force_del(cls):
		del cls.__instance__
		cls.__instance__ = None
