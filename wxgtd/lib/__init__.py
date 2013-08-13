#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
lib

Copyright (c) Karol Będkowski, 2013

"""
import os
from contextlib import contextmanager


@contextmanager
def ignore_exceptions(*exceptions):
	""" Ignored exceptions in wrapped code.

	Args:
		exceptions: ignored exceptions

	Sample:

		>>> with ignore_exceptions(OSError):
		...		os.unlink('/tmp/test')
	"""
	try:
		yield
	except exceptions:
		pass
