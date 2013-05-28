# -*- coding: utf-8 -*-
# pylint: disable-msg=R0901, R0904, C0103
""" Quick Task logic.

Copyright (c) Karol Będkowski, 2013

This file is part of wxGTD
Licence: GPLv2+
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2013"
__version__ = "2013-05-11"

import gettext
import logging

from wxgtd.model import objects as OBJ

_ = gettext.gettext
_LOG = logging.getLogger(__name__)


def create_quicktask(title):
	""" Create quick task from given title. """
	session = OBJ.Session()
	task = OBJ.Task(title=title, priority=-1)
	session.add(task)
	session.commit()
	_LOG.info("create_quicktask: ok")
	return task
