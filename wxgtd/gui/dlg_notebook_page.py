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
try:
	from wx.lib.pubsub.pub import Publisher
except ImportError:
	from wx.lib.pubsub import Publisher  # pylint: disable=E0611

from wxgtd.wxtools.validators import Validator, ValidatorDv
from wxgtd.wxtools.validators import v_length as LVALID
from wxgtd.model import objects as OBJ
from wxgtd.model import logic

from ._base_dialog import BaseDialog

_ = gettext.gettext
_LOG = logging.getLogger(__name__)


class DlgNotebookPage(BaseDialog):
	""" Edit notebook page dialog.

	Args:
		parent: parent window
	"""

	def __init__(self, parent, session, page_uuid, folder_uuid):
		BaseDialog.__init__(self, parent, 'dlg_notebook_page', save_pos=True)
		self._setup(session, page_uuid, folder_uuid)

	def _load_controls(self, wnd):
		BaseDialog._load_controls(self, wnd)

	def _create_bindings(self, wnd):
		BaseDialog._create_bindings(self, wnd)
		wnd.Bind(wx.EVT_BUTTON, self._on_delete, id=wx.ID_DELETE)

	def _setup(self, session, page_uuid, folder_uuid):
		_LOG.debug("DlgNotebookPage(%r)", (session, page_uuid, folder_uuid))
		self._session = session
		if page_uuid:
			self._page = OBJ.NotebookPage.get(self._session, uuid=page_uuid)
		else:
			if not folder_uuid or folder_uuid == '-':
				folder_uuid = None
			self._page = OBJ.NotebookPage(folder_uuid=folder_uuid)
		cb_folder = self['c_folder']
		cb_folder.Append(_("No Folder"), None)
		for folder in self._session.query(OBJ.Folder).all():
			cb_folder.Append(folder.title, folder.uuid)
		self['tc_title'].SetValidator(Validator(self._page, 'title',
				validators=LVALID.NotEmptyValidator(), field='title'))
		self['tc_note'].SetValidator(Validator(self._page, 'note'))
		self['c_folder'].SetValidator(ValidatorDv(self._page, 'folder_uuid'))

	def _on_ok(self, evt):
		if not self._wnd.Validate():
			return
		if not self._wnd.TransferDataFromWindow():
			return
		self._page.update_modify_time()
		self._session.add(self._page)
		self._session.commit()
		Publisher().sendMessage('notebook.update',
				data={'notebook_uuid': self._page.uuid})
		BaseDialog._on_ok(self, evt)

	def _on_delete(self, evt):
		uuid = self._page.uuid
		if logic.delete_notebook_page(uuid, self.wnd, self._session):
			Publisher().sendMessage('notebook.delete',
					data={'notebook_uuid': uuid})
			BaseDialog._on_close(self, evt)
