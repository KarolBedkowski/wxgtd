# -*- coding: utf-8 -*-
""" Edit task dialog.

Copyright (c) Karol Będkowski, 2013

This file is part of wxGTD
Licence: GPLv2+
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2010-2013"
__version__ = "2010-11-25"

import logging
import gettext

from wxgtd.logic import notebook as notebook_logic

from . import message_boxes as mbox

_ = gettext.gettext
_LOG = logging.getLogger(__name__)


class NotebookControler:
	""" Controller for notebooks & notebooks pages. """

	def __init__(self):
		pass

	@classmethod
	def delete_page(cls, notebook_uuid, wnd, session):
		if not mbox.message_box_delete_confirm(wnd, _("notebook page")):
			return False
		return notebook_logic.delete_notebook_page(notebook_uuid, session)
