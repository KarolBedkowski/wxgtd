# -*- coding: utf-8 -*-

"""Checklist item dialog.

Copyright (c) Karol Będkowski, 2013

This file is part of wxGTD
Licence: GPLv2+
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2013"
__version__ = "2013-04-28"

import logging
import gettext

from ._base_task_dialog import BaseTaskDialog

_ = gettext.gettext
_LOG = logging.getLogger(__name__)


class FrameChecklistitem(BaseTaskDialog):
	""" Edit checklist item dialog class.

	WARRNING: non-modal window.

	Args:
		parent: parent windows.
		task: task to edit.
		session: SqlAlchemy session.
		controller: TaskController associated to task.
	"""

	_window_name = "frame_checklistitem"

	def __init__(self, parent, task, session, controller):
		BaseTaskDialog.__init__(self, parent, task, session, controller)
