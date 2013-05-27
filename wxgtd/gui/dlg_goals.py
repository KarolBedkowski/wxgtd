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
from wxgtd.wxtools.validators import Validator, ValidatorColorStr, ValidatorDv

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
		self['tc_title'].SetValidator(Validator(self._proxy, 'title'))
		self['tc_note'].SetValidator(Validator(self._proxy, 'note'))
		self['colorselect'].SetValidator(ValidatorColorStr(self._proxy,
				'bg_color', with_alpha=True))
		self['c_timeperiod'].SetValidator(ValidatorDv(self._proxy,
				'time_period'))

	def _set_buttons_state(self):
		DictBaseDlg._set_buttons_state(self)
		item_in_edit = self._displayed_item is not None
		self['tc_title'].Enable(item_in_edit)
		self['tc_note'].Enable(item_in_edit)
		self['colorselect'].Enable(item_in_edit)
		self['c_timeperiod'].Enable(item_in_edit)

	def _setup_combobox(self):
		c_timeperiod = self["c_timeperiod"]
		c_timeperiod.Clear()
		for key, name in enums.GOAL_TIME_TERM.iteritems():
			c_timeperiod.Append(name, key)
