# -*- coding: utf-8 -*-
""" Edit goals dialog.

Copyright (c) Karol Będkowski, 2013

This file is part of wxGTD
Licence: GPLv2+
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2013"
__version__ = "2013-04-14"

import gettext

from wxgtd.model import objects as OBJ
from wxgtd.model import enums
from wxgtd.wxtools.validators import ValidatorDv

from ._dict_base_dlg import DictBaseDlg

_ = gettext.gettext


class DlgGoals(DictBaseDlg):
	""" Edit goals dialog.
	"""

	_items_list_control = "lb_goals"
	_item_name = _("goal")
	_item_class = OBJ.Goal

	def __init__(self, parent):
		DictBaseDlg.__init__(self, parent, 'dlg_goals')
		self._setup_combobox()

	def _load_controls(self, wnd):
		DictBaseDlg._load_controls(self, wnd)
		self['c_timeperiod'].SetValidator(ValidatorDv(self._proxy,
				'time_period'))

	def _set_buttons_state(self):
		DictBaseDlg._set_buttons_state(self)
		item_in_edit = self._displayed_item is not None
		self['c_timeperiod'].Enable(item_in_edit)

	def _setup_combobox(self):
		c_timeperiod = self["c_timeperiod"]
		c_timeperiod.Clear()
		for key, name in enums.GOAL_TIME_TERM.iteritems():
			c_timeperiod.Append(name, key)
