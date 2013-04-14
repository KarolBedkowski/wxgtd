# -*- coding: utf-8 -*-

""" Okno edycji tagów
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2013"
__version__ = "2013-04-14"

import gettext
import logging

#import wx

from wxgtd.model import objects as OBJ
from wxgtd.wxtools.validators import Validator, ValidatorColorStr

from _dict_base_dlg import DictBaseDlg

_LOG = logging.getLogger(__name__)
_ = gettext.gettext


class DlgTags(DictBaseDlg):

	_items_list_control = "lb_tags"
	_item_name = _("tag")
	_item_class = OBJ.Tag

	def __init__(self, parent):
		DictBaseDlg.__init__(self, parent, 'dlg_tags')

	def _load_controls(self, wnd):
		DictBaseDlg._load_controls(self, wnd)
		self['tc_title'].SetValidator(Validator(self._proxy, 'title'))
		self['tc_note'].SetValidator(Validator(self._proxy, 'note'))
		self['colorselect'].SetValidator(ValidatorColorStr(self._proxy,
				'bg_color'))

	def _set_buttons_state(self):
		DictBaseDlg._set_buttons_state(self)
		item_in_edit = self._displayed_item is not None
		self['tc_title'].Enable(item_in_edit)
		self['tc_note'].Enable(item_in_edit)
		self['colorselect'].Enable(item_in_edit)
