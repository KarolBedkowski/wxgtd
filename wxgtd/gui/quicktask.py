# -*- coding: utf-8 -*-
# pylint: disable-msg=R0901, R0904, C0103
""" Quick Task actions.

Copyright (c) Karol Będkowski, 2013

This file is part of wxGTD
Licence: GPLv2+
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2013"
__version__ = "2013-05-11"

import gettext
import logging

import wx
try:
	from wx.lib.pubsub.pub import Publisher
except ImportError:
	from wx.lib.pubsub import Publisher  # pylint: disable=E0611

from wxgtd.model import objects as OBJ

_ = gettext.gettext
_LOG = logging.getLogger(__name__)


def quick_task(self, parent_wnd=None):
	dlg = wx.TextEntryDialog(parent_wnd, _("Enter task title"),
			_("wxGTD Quick Task"), "")
	if dlg.ShowModal() == wx.ID_OK and dlg.GetValue().strip():
		session = OBJ.Session()
		task = OBJ.Task(title=dlg.GetValue().strip(), priority=-1)
		session.add(task)
		session.commit()
		Publisher().sendMessage('task.update', data={'task_uuid': task.uuid})
	dlg.Destroy()
