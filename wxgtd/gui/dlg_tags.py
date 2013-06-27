# -*- coding: utf-8 -*-
""" Tags edit dialog.

Copyright (c) Karol Będkowski, 2013

This file is part of wxGTD
Licence: GPLv2+
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2013"
__version__ = "2013-04-28"

import gettext

from wxgtd.model import objects as OBJ

from ._dict_base_dlg import DictBaseDlg

_ = gettext.gettext


class DlgTags(DictBaseDlg):
	""" Tags edit dialog.
	"""

	_items_list_control = "lb_tags"
	_item_name = _("tag")
	_item_class = OBJ.Tag

	def __init__(self, parent):
		DictBaseDlg.__init__(self, parent, 'dlg_tags')
