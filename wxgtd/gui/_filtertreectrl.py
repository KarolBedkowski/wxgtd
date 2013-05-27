# -*- coding: utf-8 -*-
## pylint: disable=W0401,C0103,W0141
""" Filter tree widget.

Copyright (c) Karol Będkowski, 2013

This file is part of wxGTD
Licence: GPLv2+
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
from wxgtd.model import enums
from wxgtd.lib import appconfig

_ = gettext.gettext

NODE_NORMAL = 0
NODE_CHECKBOX = 1
NODE_RADIO = 2


class TreeItem(object):
	"""Single tree item"""
	# pylint: disable=R0903

	def __init__(self, title, obj, *childs):
		self.title = title
		self.obj = obj
		self.childs = childs
		self.node_type = NODE_NORMAL

	def __repr__(self):
		return '<%r title=%r, obj=%r, type=%r, childs_count=%d>' % (self.__class__,
				self.title, self.obj, self.node_type, len(self.childs))

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

	def __repr__(self):
		return '<%r title=%r, obj=%r, type=%r, checked=%r, childs_count=%d>' % (
				self.__class__, self.title, self.obj, self.node_type, self.checked,
				len(self.childs))

	def get_item(self, indices):
		if len(indices) == 1:
			return self.childs[indices[0]]
		return self.childs[indices[0]].get_item(indices[1:])

	def set_child_check(self, check):
		for child in self.childs:
			if hasattr(child, 'checked'):
				child.checked = check


class FilterTreeModel(object):
	""" Model used in FilterTreeModel. """

	def __init__(self):
		self._items = []
		self._items.append(TreeItemCB(_("Statuses"), "STATUSES",
				*tuple(TreeItemCB(status, status_id or 0)
						for status_id, status
						in enums.STATUSES.iteritems())))
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
		self._load_last_settings()

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

	def check_items(self, obj, ids):
		items = [item for item in self._items if item.obj == obj]
		if not items:
			return
		parent = items[0]
		checked_cnt = 0
		for item in parent.childs:
			if item.obj in ids:
				item.checked = True
				checked_cnt += 1
		parent.checked = checked_cnt == len(parent.childs)

	def _load_last_settings(self):
		appcfg = appconfig.AppConfig()

		def convert(ids, func=str):
			for id_ in ids:
				yield None if id_ is None or id_ == 'None' else func(id_)

		statuses = appcfg.get('last_filter', 'statuses', None)
		if statuses:
			ids = set(convert(statuses.split(','), int))
			self.check_items("STATUSES", ids)
		contexts = appcfg.get('last_filter', 'contexts', None)
		if contexts:
			ids = set(convert(contexts.split(',')))
			self.check_items("CONTEXTS", ids)
		folders = appcfg.get('last_filter', 'folders', None)
		if folders:
			ids = set(convert(folders.split(',')))
			self.check_items("FOLDERS", ids)
		goals = appcfg.get('last_filter', 'goals', None)
		if goals:
			ids = set(convert(goals.split(',')))
			self.check_items("GOALS", ids)
		tags = appcfg.get('last_filter', 'tags', None)
		if tags:
			ids = set(convert(tags.split(',')))
			self.check_items("TAGS", ids)


class FilterTreeCtrl(treemixin.VirtualTree, treemixin.ExpansionState,
		CT.CustomTreeCtrl):
	""" TreeControl with checboxes allows to filter elements to show. """
	# pylint: disable=R0901

	def __init__(self, *args, **kwargs):
		self._model = FilterTreeModel()
		kwargs['style'] = wx.TR_HIDE_ROOT | \
			wx.TR_HAS_BUTTONS | wx.TR_FULL_ROW_HIGHLIGHT
		kwargs['agwStyle'] = CT.TR_DEFAULT_STYLE | wx.TR_HIDE_ROOT
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

	def OnGetItemText(self, indices, *_args, **_kwargs):
		return self._model.get_text(indices)

	def OnGetChildrenCount(self, indices):
		return self._model.get_children_count(indices)

	def _on_item_checked(self, event):
		item = event.GetItem()
		indices = self.GetIndexOfItem(item)
		if self.GetItemType(item) == 2:  # radio
			pass
		elif self.GetItemType(item) == 1:  # checkbox
			# checkbox - select or unselect all sub-items
			self._model.get_item(indices).checked = item.GetValue()
			if len(indices) == 1:
				# zaznaczanie / odznaczanie podzadań
				value = item.GetValue()
				self._model.get_item(indices).set_child_check(value)
				for child in item.GetChildren():
					child.Check(value)
			#self.AutoCheckChild(item, item.GetValue())
			self.RefreshSubtree(item)
		event.Skip()

	def refresh(self):
		""" Refresh tree. """
		self.ExpandAll()
		wx.CallAfter(self.RefreshItems)

	def save_last_settings(self):
		appcfg = appconfig.AppConfig()
		statuses = self._model.checked_items_by_parent("STATUSES")
		appcfg.set('last_filter', 'statuses', ','.join(map(str, statuses)))
		contexts = self._model.checked_items_by_parent("CONTEXTS")
		appcfg.set('last_filter', 'contexts', ','.join(map(str, contexts)))
		folders = self._model.checked_items_by_parent("FOLDERS")
		appcfg.set('last_filter', 'folders', ','.join(map(str, folders)))
		goals = self._model.checked_items_by_parent("GOALS")
		appcfg.set('last_filter', 'goals', ','.join(map(str, goals)))
		tags = self._model.checked_items_by_parent("TAGS")
		appcfg.set('last_filter', 'tags', ','.join(map(str, tags)))
