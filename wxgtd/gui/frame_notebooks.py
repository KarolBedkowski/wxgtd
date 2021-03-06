# -*- coding: utf-8 -*-
""" Notebook frame.

Copyright (c) Karol Będkowski, 2013

This file is part of wxGTD
Licence: GPLv2+
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2013"
__version__ = "2013-05-23"

import gettext
import logging

import wx
import wx.lib.dialogs

from wxgtd.wxtools.wxpub import publisher
from wxgtd.wxtools import iconprovider
from wxgtd.wxtools import wxutils
from wxgtd.model import objects as OBJ
from wxgtd.lib import fmt
from wxgtd.gui._base_frame import BaseFrame
from wxgtd.gui.notebook_controller import NotebookController

_ = gettext.gettext
ngettext = gettext.ngettext  # pylint: disable=C0103
_LOG = logging.getLogger(__name__)


class FrameNotebook(BaseFrame):
	""" Notebook window class. """
	# pylint: disable=R0903, R0902

	_xrc_resource = 'wxgtd.xrc'
	_window_name = 'frame_notebook'
	_window_icon = 'wxgtd'
	_instance = None

	def __init__(self):
		BaseFrame.__init__(self)
		self._setup()

	@classmethod
	def run(cls):
		if cls._instance is not None:
			cls._instance.wnd.Raise()
		else:
			cls._instance = FrameNotebook()
			cls._instance.wnd.Show()

	def _setup(self):
		self._pages_uuid = {}
		self._current_sort_col = None
		self._current_sort_ord = 1
		self._session = OBJ.Session()
		self._lb_pages.InsertColumn(0, _("Title"))
		self._lb_pages.InsertColumn(1, _("Created"))
		self._lb_pages.InsertColumn(2, _("Modified"))
		self._refresh_folders()
		self._lb_folders.Select(0)
		self._refresh_pages()

	def _load_controls(self):
		# pylint: disable=W0201
		BaseFrame._load_controls(self)
		# filter tree ctrl
		self._lb_folders = self['lb_folders']
		self._lb_pages = wx.ListCtrl(self['pages_panel'], -1, style=wx.LC_REPORT)

		box = wx.BoxSizer()
		box.Add(self._lb_pages, 1, wx.EXPAND | wx.ALL, 12)
		self['pages_panel'].SetSizer(box)

	def _create_bindings(self, wnd):
		BaseFrame._create_bindings(self, wnd)
		wnd.Bind(wx.EVT_LISTBOX, self._on_folders_listbox, self._lb_folders)
		wnd.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self._on_pages_list_activated,
				self._lb_pages)
		wnd.Bind(wx.EVT_LIST_COL_CLICK, self._on_pages_list_col_click)
		publisher.subscribe(self._on_notebook_update, ('notebook', 'update'))
		publisher.subscribe(self._on_notebook_update, ('notebook', 'delete'))

	def _create_toolbar(self):
		toolbar = self.wnd.CreateToolBar()
		tbi = toolbar.AddLabelTool(-1, _('New Note'),
				iconprovider.get_image("task_new"),
				shortHelp=_('Add new notebook page'))
		self.wnd.Bind(wx.EVT_TOOL, self._on_btn_new_page, id=tbi.GetId())

		tbi = toolbar.AddLabelTool(-1, _('Edit Note'),
				iconprovider.get_image('task_edit'),
				shortHelp=_('Edit selected notebook page'))
		self.wnd.Bind(wx.EVT_TOOL, self._on_btn_edit_page,
				id=tbi.GetId())

		tbi = toolbar.AddLabelTool(-1, _('Delete Note'),
				iconprovider.get_image('task_delete'),
				shortHelp=_('Delete selected notebook page'))
		self.wnd.Bind(wx.EVT_TOOL, self._on_btn_delete_page,
				id=tbi.GetId())

		toolbar.AddSeparator()

		tbi = toolbar.AddLabelTool(-1, _('Exit'),
			iconprovider.get_image("exit"),
			shortHelp=_('Close window'))
		self.wnd.Bind(wx.EVT_TOOL, self._on_btn_close, id=tbi.GetId())

		toolbar.Realize()

	def _set_size_pos(self):
		BaseFrame._set_size_pos(self)
		self['window_1'].SetSashGravity(0.0)
		self['window_1'].SetMinimumPaneSize(20)
		self['window_1'].SetSashPosition(self._appconfig.get('frame_notebooks',
				'win1', 200))

	# events

	def _on_close(self, event):
		self._appconfig.set('frame_notebook', 'win1', self['window_1']
				.GetSashPosition())
		FrameNotebook._instance = None
		BaseFrame._on_close(self, event)

	def _on_btn_close(self, _evt):
		self.wnd.Close()

	def _on_btn_new_page(self, _evt):
		NotebookController.new_page(self.wnd, self.selected_folder_uuid)

	def _on_btn_edit_page(self, _evt):
		uuid = self.selected_page_uuid
		if uuid:
			NotebookController.open_page(self.wnd, uuid)

	def _on_btn_delete_page(self, _evt):
		uuid = self.selected_page_uuid
		if uuid:
			NotebookController(self.wnd, self._session, None).delete_page(uuid)

	def _on_folders_listbox(self, _evt):
		self._refresh_pages()

	def _on_notebook_update(self, _evt):
		self._refresh_folders()
		self._refresh_pages()

	def _on_pages_list_activated(self, evt):
		uuid = self._pages_uuid[evt.GetData()]
		NotebookController.open_page(self.wnd, uuid)

	def _on_pages_list_col_click(self, evt):
		m_col = evt.m_col
		if self._current_sort_col == m_col:
			self._current_sort_ord = -self._current_sort_ord
		else:
			self._current_sort_col = m_col
			self._current_sort_ord = 1
		self._refresh_pages()

	@property
	def selected_folder_uuid(self):
		return self._lb_folders.GetClientData(self._lb_folders.GetSelection())

	@property
	def selected_page_uuid(self):
		idx = self._lb_pages.GetNextItem(-1, wx.LIST_NEXT_ALL,
				wx.LIST_STATE_SELECTED)
		if idx == -1:
			return
		return self._pages_uuid[self._lb_pages.GetItemData(idx)]

	@wxutils.wait_cursor
	def _refresh_folders(self):
		self._session.expire_all()  # pylint: disable=E1101
		to_sel = self._lb_folders.GetSelection()
		self._lb_folders.Clear()
		self._lb_pages.DeleteAllItems()
		all_cnt = self._session.query(OBJ.NotebookPage).filter(
				OBJ.NotebookPage.deleted.is_(None)).count()
		cnt_str = ("  (%d)" % all_cnt) if all_cnt else ""
		self._lb_folders.Append(_("Any Folder") + cnt_str, "-")
		no_folder_cnt = self._session.query(OBJ.NotebookPage)\
				.filter(OBJ.NotebookPage.folder_uuid.is_(None),
						OBJ.NotebookPage.deleted.is_(None)).count()
		cnt_str = ("  (%d)" % no_folder_cnt) if no_folder_cnt else ""
		self._lb_folders.Append(_("No Folder") + cnt_str, None)
		for folder in (self._session.query(OBJ.Folder)
				.filter(OBJ.Folder.deleted.is_(None))
				.order_by(OBJ.Folder.title)):
			title = folder.title
			cnt = len(folder.notebook_pages)
			if cnt > 0:
				title += "  (" + str(cnt) + ")"
			self._lb_folders.Append(title, folder.uuid)
		self._lb_folders.Select(to_sel)

	@wxutils.wait_cursor
	def _refresh_pages(self):
		self._session.expire_all()  # pylint: disable=E1101
		sel_folder = self.selected_folder_uuid
		self._lb_pages.DeleteAllItems()
		self._pages_uuid.clear()
		query = self._session.query(OBJ.NotebookPage)\
				.filter(OBJ.NotebookPage.deleted.is_(None))
		if sel_folder is None:
			query = query.filter(OBJ.NotebookPage.folder_uuid.is_(None))
		elif sel_folder != '-':
			query = query.filter(OBJ.NotebookPage.folder_uuid == sel_folder)
		col = [OBJ.NotebookPage.title, OBJ.NotebookPage.created,
				OBJ.NotebookPage.modified][self._current_sort_col or 0]
		if self._current_sort_ord == 1:
			query = query.order_by(col.asc())
		else:
			query = query.order_by(col.desc())
		idx = 0
		for idx, page in enumerate(query):
			self._lb_pages.InsertStringItem(idx, page.title)
			self._lb_pages.SetStringItem(idx, 1,
					fmt.format_timestamp(page.created))
			self._lb_pages.SetStringItem(idx, 2,
					fmt.format_timestamp(page.modified))
			self._lb_pages.SetItemData(idx, idx)
			self._pages_uuid[idx] = page.uuid

		self.wnd.SetStatusText(ngettext("%d item", "%d items", idx) % idx, 1)
		self._lb_pages.SetColumnWidth(0, wx.LIST_AUTOSIZE)
		self._lb_pages.SetColumnWidth(1, wx.LIST_AUTOSIZE)
		self._lb_pages.SetColumnWidth(2, wx.LIST_AUTOSIZE)
