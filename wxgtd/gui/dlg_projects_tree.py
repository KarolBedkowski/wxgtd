# -*- coding: utf-8 -*-
""" Dialog for selecting projects / checklists

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

from wxgtd.model import objects as OBJ
from wxgtd.model import enums
from wxgtd.wxtools import iconprovider

from ._base_dialog import BaseDialog

_ = gettext.gettext
_LOG = logging.getLogger(__name__)


class DlgProjectTree(BaseDialog):
	""" Dialog for selecting projects / checlists.

	Args:
		parent: parent window
		timestamp: date and time as long or datetime
		timeset: boolean - is time is set.
	"""

	def __init__(self, parent, session):
		BaseDialog.__init__(self, parent, 'dlg_projects_tree', save_pos=True)
		self._setup(session)

	@property
	def selected(self):
		sel = self._tc_tree.GetSelection()
		return self._tc_tree.GetPyData(sel) if sel else None

	def _load_controls(self, wnd):
		BaseDialog._load_controls(self, wnd)
		self._tc_tree = self['tc_projects']
		self._icons = iconprovider.IconProvider()
		self._icons.load_icons(['project_small', 'checklist_small'])
		self._tc_tree.SetImageList(self._icons.image_list)

	def _create_bindings(self, wnd):
		BaseDialog._create_bindings(self, wnd)

	def _setup(self, session):
		self._session = session
		self._fill_projects()

	def _on_ok(self, evt):
		if self._tc_tree.GetSelection():
			BaseDialog._on_ok(self, evt)

	def _fill_projects(self):
		tc_tree = self._tc_tree
		tree_root = tc_tree.AddRoot(_("wxGTD (no project)"))
		tc_tree.SetPyData(tree_root, None)
		icon_project_idx = self._icons.get_image_index('project_small')
		icon_checklist_idx = self._icons.get_image_index('checklist_small')

		def add_item(root, task):
			child = tc_tree.AppendItem(root, task.title)
			tc_tree.SetPyData(child, task.uuid)
			icon = (icon_project_idx if task.type == enums.TYPE_PROJECT
					else icon_checklist_idx)
			tc_tree.SetItemImage(child, icon, wx.TreeItemIcon_Normal)
			tc_tree.SetItemImage(child, icon, wx.TreeItemIcon_Expanded)
			for subtask in task.sub_project_or_checklists:
				add_item(child, subtask)

		for obj in OBJ.Task.root_projects_checklists(self._session):
			add_item(tree_root, obj)

		tc_tree.ExpandAll()
