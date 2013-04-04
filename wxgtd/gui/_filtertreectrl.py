# -*- coding: utf-8 -*-
"""
Główne okno programu
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2013"
__version__ = "2013-03-10"

import gettext

import wx

import wx.lib.customtreectrl as CT
import wx.gizmos
from wx.lib.mixins import treemixin
from wxgtd.model import objects as OBJ


_ = gettext.gettext

NODE_NORMAL = 0
NODE_CHECKBOX = 1
NODE_RADIO = 2


class TreeItem(object):
	"""Single tree item"""
	def __init__(self, title, obj, *childs):
		self.title = title
		self.obj = obj
		self.childs = childs
		self.node_type = NODE_NORMAL

	def get_item(self, indices):
		if len(indices) == 1:
			return self.childs[indices[0]]
		return self.childs[indices[0]].get_item(indices[1:])


class TreeItemCB(TreeItem):
	"""Checkbox tree item"""
	def __init__(self, *args, **kwargs):
		TreeItem.__init__(self, *args, **kwargs)
		self.node_type = NODE_CHECKBOX
		self.checked = False

	def get_item(self, indices):
		if len(indices) == 1:
			return self.childs[indices[0]]
		return self.childs[indices[0]].get_item(indices[1:])

	def set_child_check(self, check):
		print 'set_child_check', check
		for child in self.childs:
			if hasattr(child, 'checked'):
				child.checked = check


class FilterTreeModel(object):
	def __init__(self):
		self._items = []
		self._items.append(TreeItemCB(_("Statuses"), "STATUSES",
				*tuple(TreeItemCB(status, status_id or 0)
						for status_id, status
						in OBJ.STATUSES.iteritems())))
		self._items.append(TreeItemCB(_("Contexts"), "CONTEXTS",
				TreeItemCB(_("No Context"), None),
				*tuple(TreeItemCB(context.title, context.uuid)
						for context in OBJ.Context.all())))
		self._items.append(TreeItemCB(_("Folders"), "FOLDERS",
				TreeItemCB(_("No Folder"), None),
				*tuple(TreeItemCB(folder.title, folder.uuid)
						for folder in OBJ.Folder.all())))
		self._items.append(TreeItemCB(_("Goals"), "GOALS",
				TreeItemCB(_("No goal"), None),
				*tuple(TreeItemCB(goal.title, goal.uuid)
						for goal in OBJ.Goal.all())))
		self._items.append(TreeItemCB(_("Tags"), "TAGS",
				TreeItemCB(_("No tag"), None),
				*tuple(TreeItemCB(tag.title, tag.uuid)
						for tag in OBJ.Tag.all())))

	def get_item(self, indices):
		if len(indices) == 1:
			return self._items[indices[0]]
		return self._items[indices[0]].get_item(indices[1:])

	def get_text(self, indices):
		if not indices:
			return 'root'  # hidden root
		return self.get_item(indices).title

	def get_children_count(self, indices):
		if not indices:
			return len(self._items)
		return len(self.get_item(indices).childs)

	def get_item_type(self, indices):
		""" get item type: 1=checkbox; 2=radiom, 0=text """
		if not indices:
			return 0
		return self.get_item(indices).node_type

	def checked_items_by_parent(self, obj):
		items = [item for item in self._items if item.obj == obj]
		if not items:
			return []
		return (item.obj for item in items[0].childs
				if hasattr(item, 'checked') and item.checked)


class FilterTreeCtrl(treemixin.VirtualTree, treemixin.ExpansionState,
		CT.CustomTreeCtrl):

	def __init__(self, *args, **kwargs):
		self._model = FilterTreeModel()
		kwargs['style'] = wx.TR_HIDE_ROOT | \
			wx.TR_HAS_BUTTONS | wx.TR_FULL_ROW_HIGHLIGHT
		kwargs['agwStyle'] = CT.TR_DEFAULT_STYLE | CT.TR_AUTO_CHECK_CHILD | \
			CT.TR_AUTO_CHECK_PARENT | CT.TR_AUTO_TOGGLE_CHILD | wx.TR_HIDE_ROOT
		super(FilterTreeCtrl, self).__init__(*args, **kwargs)
		self.Bind(CT.EVT_TREE_ITEM_CHECKED, self._on_item_checked)
		wx.CallAfter(self.refresh)

	@property
	def model(self):
		return self._model

	def OnGetItemType(self, indices):
		return self._model.get_item_type(indices)

	def OnGetItemChecked(self, indices):
		item = self._model.get_item(indices)
		return hasattr(item, 'checked') and item.checked

	def OnGetItemText(self, indices):
		return self._model.get_text(indices)

	def OnGetChildrenCount(self, indices):
		return self._model.get_children_count(indices)

	def _on_item_checked(self, event):
		item = event.GetItem()
		indices = self.GetIndexOfItem(item)
		if self.GetItemType(item) == 2:
			# It's a radio item; reset other items on the same level
			#for nr in range(self.get_children_count(self.GetItemParent(item))):
			pass
			#self.checked[itemIndex[:-1] + (nr, )] = False
		elif self.GetItemType(item) == 1:
			# checkbox - select or unselect all sub-items
			self._model.get_item(indices).checked = item.GetValue()
			#self._model.get_item(indices).set_child_check(item.GetValue())
			#self.AutoCheckChild(item, item.GetValue())
			self.RefreshSubtree(item)
		event.Skip()

	def refresh(self):
		self.ExpandAll()
		wx.CallAfter(self.RefreshItems)
