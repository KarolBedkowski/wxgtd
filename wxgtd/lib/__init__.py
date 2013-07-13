#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
lib

Copyright (c) Karol Będkowski, 2013

"""
import os
from contextlib import contextmanager


def two_elements_iter(seq, return_last=False):
	prev = None
	for item in seq:
		if prev is not None:
			yield prev, item
		prev = item
	if return_last:
		yield prev, None


@contextmanager
def ignore_exceptions(*exceptions):
	""" Ignored exceptions in wrapped code.

	Args:
		exceptions: ignored exceptions

	Sample:

		>>> with ignore_exceptions(OSError):
		... 	os.unlink('/tmp/test')
	"""
	try:
		yield
	except exceptions:
		pass
