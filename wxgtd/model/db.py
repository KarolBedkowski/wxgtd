# -*- coding: utf-8 -*-

"""
Obiekt bazy dany - dostęp do danych

TODO: przenieść całe tworzenie obiektów z sqlite
"""
from __future__ import with_statement

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2009-2013"
__version__ = "2011-05-15"


import logging

_LOG = logging.getLogger(__name__)


class Db(object):
	"""docstring for Db"""

	def __init__(self, filename):
		self.filename = filename

	def open(self):
		"""Open database"""
		# TODO: write code...

	def close(self):
		"""Close database"""
		# TODO: write code...
