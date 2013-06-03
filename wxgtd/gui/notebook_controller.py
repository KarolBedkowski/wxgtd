# -*- coding: utf-8 -*-
""" Notebooks controller.

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
from wxgtd.model import objects as OBJ
from wxgtd.gui.dlg_notebook_page import DlgNotebookPage

from . import message_boxes as mbox

_ = gettext.gettext
_LOG = logging.getLogger(__name__)


class NotebookController:
	""" Controller for notebooks & notebooks pages. """

	_controllers = {}

	def __init__(self, parent_wnd, session, page):
		self._session = session
		self._parent_wnd = parent_wnd
		self._page = page
		self._dialog = None

	def open_dialog(self):
		""" Open dialog or raise existing. """
		if self._dialog is None:
			self._dialog = DlgNotebookPage(self._parent_wnd, self._session,
					self._page, self)
		self._dialog.run()

	def close(self):
		""" Close current page controller. """
		if self._page.uuid in self._controllers:
			del self._controllers[self._page.uuid]
		self._session.close()

	@property
	def wnd(self):
		""" Get current wx windows. """
		return (self._dialog and self._dialog.wnd) or self._parent_wnd or None

	def delete_page(self, uuid=None):
		""" Delete current or given notebook page. """
		if not mbox.message_box_delete_confirm(self.wnd, _("notebook page")):
			return False
		uuid = uuid or self._page.uuid
		return notebook_logic.delete_notebook_page(uuid, self._session)

	@classmethod
	def open_page(cls, parent_wnd, page_uuid):
		""" Open dialog for given page. """
		if page_uuid in cls._controllers:
			cls._controllers[page_uuid].open_dialog()
			return
		session = OBJ.Session()
		page = OBJ.NotebookPage.get(session=session, uuid=page_uuid)
		contr = NotebookController(parent_wnd, session, page)
		cls._controllers[page_uuid] = contr
		contr.open_dialog()

	@classmethod
	def new_page(cls, parent_wnd, folder_uuid=None):
		""" Open dialog with new page.  """
		session = OBJ.Session()
		if not folder_uuid or folder_uuid == '-':
			folder_uuid = None
		page = OBJ.NotebookPage(folder_uuid=folder_uuid)
		contr = NotebookController(parent_wnd, session, page)
		contr.open_dialog()
