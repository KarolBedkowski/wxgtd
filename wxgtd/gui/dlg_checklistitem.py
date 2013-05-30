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

from wxgtd.model import objects as OBJ
from wxgtd.model import enums

from ._base_task_dialog import BaseTaskDialog

_ = gettext.gettext
_LOG = logging.getLogger(__name__)


class DlgChecklistitem(BaseTaskDialog):
	""" Edit checllist item dialog class.

	WARRNING: non-modal window.

	Args:
		parent: parent window
		task_uuid: uuid task for edit; if empty - create new task
		parent_uuid: parent task uuid.
	"""

	def __init__(self, parent, task_uuid, parent_uuid=None):
		BaseTaskDialog.__init__(self, parent, 'dlg_checklistitem',
				task_uuid, parent_uuid)

	def _load_task(self, task_uuid):
		return self._session.query(  # pylint: disable=E1101
				OBJ.Task).filter_by(uuid=task_uuid).first()

	def _create_task(self, parent_uuid):
		# find last importance in this checlist
		importance = OBJ.Task.find_max_importance(parent_uuid, self._session)
		task = OBJ.Task(type=enums.TYPE_CHECKLIST_ITEM,
					parent_uuid=parent_uuid,
					importance=importance + 1)
		return task
