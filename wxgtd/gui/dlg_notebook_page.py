# -*- coding: utf-8 -*-
""" Remind setting dialog.

Copyright (c) Karol Będkowski, 2013

This file is part of wxGTD
Licence: GPLv2+
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2013"
__version__ = "2013-04-28"

import logging
import gettext

import wx

from wxgtd.wxtools.validators import Validator, ValidatorDv
from wxgtd.wxtools.validators import v_length as LVALID
from wxgtd.model import objects as OBJ
from wxgtd.logic import notebook as notebook_logic

from ._base_dialog import BaseDialog

_ = gettext.gettext
_LOG = logging.getLogger(__name__)


class DlgNotebookPage(BaseDialog):
	""" Edit notebook page dialog.

	Args:
		parent: parent window
	"""

	def __init__(self, parent, session, page, controller):
		BaseDialog.__init__(self, parent, 'dlg_notebook_page', save_pos=True)
		self._controller = controller
		self._setup(session, page)

	def _load_controls(self, wnd):
		BaseDialog._load_controls(self, wnd)

	def _create_bindings(self, wnd):
		BaseDialog._create_bindings(self, wnd)
		wnd.Bind(wx.EVT_BUTTON, self._on_delete, id=wx.ID_DELETE)

	def _setup(self, session, page):
		_LOG.debug("DlgNotebookPage(%r)", page)
		self._session = session
		self._page = page
		self._original_page = self._page.clone(cleanup=False)
		cb_folder = self['c_folder']
		cb_folder.Append(_("No Folder"), None)
		for folder in OBJ.Folder.all(session=self._session, order_by='title'):
			cb_folder.Append(folder.title, folder.uuid)
		self['tc_title'].SetValidator(Validator(self._page, 'title',
				validators=LVALID.NotEmptyValidator(), field='title'))
		self['tc_note'].SetValidator(Validator(self._page, 'note'))
		self['c_folder'].SetValidator(ValidatorDv(self._page, 'folder_uuid'))

	def _on_close(self, evt):
		self._controller.close()
		BaseDialog._on_close(self, evt)

	def _on_ok(self, evt):
		if not self._wnd.Validate():
			return
		if not self._wnd.TransferDataFromWindow():
			return
		if notebook_logic.save_modified_page(self._page, self._session):
			BaseDialog._on_ok(self, evt)

	def _on_delete(self, evt):
		if self._controller.delete_page():
			BaseDialog._on_close(self, evt)

	def _data_changed(self):
		if not self._wnd.TransferDataFromWindow():
			return False
		return not self._original_page.compare(self._page)
