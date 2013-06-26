# -*- coding: utf-8 -*-
""" Edit folders dialog.

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


class DlgFolders(DictBaseDlg):
	""" Edit folders dialog.
	"""

	_items_list_control = "lb_folders"
	_item_name = _("folder")
	_item_class = OBJ.Folder

	def __init__(self, parent):
		DictBaseDlg.__init__(self, parent, 'dlg_folders')
