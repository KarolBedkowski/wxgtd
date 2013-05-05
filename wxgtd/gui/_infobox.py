# -*- coding: utf-8 -*-
## pylint: disable-msg=W0401, C0103
"""Info box draw function.

Copyright (c) Karol Będkowski, 2013

This file is part of wxGTD
Licence: GPLv2+
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2013"
__version__ = "2011-03-29"

import gettext
import logging

import wx

from wxgtd.model import enums
from wxgtd.wxtools import iconprovider

_ = gettext.gettext
_LOG = logging.getLogger(__name__)


def draw_info(mdc, task, overdue):
	font_task = wx.Font(10, wx.NORMAL, wx.NORMAL, wx.BOLD, False)
	font_info = wx.Font(8, wx.NORMAL, wx.NORMAL, wx.NORMAL, False)
	inf_y_offset = mdc.GetTextExtent("Agw")[1] + 10

	mdc.SetTextForeground(wx.RED if overdue else wx.BLACK)
	mdc.SetFont(font_task)
	mdc.DrawText(task.title, 0, 5)
	mdc.SetFont(font_info)
	inf_x_offset = 0
	if task.status:
		mdc.DrawBitmap(iconprovider.get_image('status_small'), inf_x_offset,
				inf_y_offset, False)
		inf_x_offset += 15  # 12=icon
		status_text = enums.STATUSES[task.status]
		mdc.DrawText(status_text, inf_x_offset, inf_y_offset)
		inf_x_offset += mdc.GetTextExtent(status_text)[0] + 10
	if task.context:
		context = task.context.title
		mdc.DrawText(context, inf_x_offset, inf_y_offset)
		inf_x_offset += mdc.GetTextExtent(context)[0] + 10
	if task.parent:
		mdc.DrawBitmap(iconprovider.get_image('project_small'), inf_x_offset,
				inf_y_offset, False)
		inf_x_offset += 15  # 12=icon
		parent = task.parent.title
		mdc.DrawText(parent, inf_x_offset, inf_y_offset)
		inf_x_offset += mdc.GetTextExtent(parent)[0] + 10
	if task.goal:
		mdc.DrawBitmap(iconprovider.get_image('goal_small'), inf_x_offset,
				inf_y_offset, False)
		inf_x_offset += 15  # 12=icon
		goal = task.goal.title
		mdc.DrawText(goal, inf_x_offset, inf_y_offset)
		inf_x_offset += mdc.GetTextExtent(goal)[0] + 10
	if task.folder:
		mdc.DrawBitmap(iconprovider.get_image('folder_small'), inf_x_offset,
				inf_y_offset, False)
		inf_x_offset += 15  # 12=icon
		folder = task.folder.title
		mdc.DrawText(folder, inf_x_offset, inf_y_offset)
		inf_x_offset += mdc.GetTextExtent(folder)[0] + 10
	if task.tags:
		mdc.DrawBitmap(iconprovider.get_image('tag_small'), inf_x_offset,
				inf_y_offset, False)
		inf_x_offset += 15  # 12=icon
		tags = ",".join(tasktag.tag.title for tasktag in task.tags)
		mdc.DrawText(tags, inf_x_offset, inf_y_offset)
		inf_x_offset += mdc.GetTextExtent(tags)[0] + 10
