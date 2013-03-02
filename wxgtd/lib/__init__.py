#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
lib

Copyright (c) Karol Będkowski, 2013

"""


def two_elements_iter(seq, return_last=False):
	prev = None
	for item in seq:
		if prev is not None:
			yield prev, item
		prev = item
	if return_last:
		yield prev, None
