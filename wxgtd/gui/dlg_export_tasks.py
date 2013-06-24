# -*- coding: utf-8 -*-
""" Export setting dialog.

Copyright (c) Karol Będkowski, 2013

This file is part of wxGTD
Licence: GPLv2+
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2013"
__version__ = "2013-06-24"

import logging
import gettext
import os

import wx

from wxgtd.wxtools.validators import Validator
from wxgtd.wxtools.validators import v_length as LVALID
from wxgtd.model import exporter

from ._base_dialog import BaseDialog

_ = gettext.gettext
_LOG = logging.getLogger(__name__)


class DlgExportTasks(BaseDialog):
	""" Exporting task parameters dialog.

	Args:
		parent: parent window
		tasks: list of task to export
	"""

	def __init__(self, parent, tasks):
		BaseDialog.__init__(self, parent, 'dlg_export_tasks')
		self._tasks = tasks
		self._setup()

	def _create_bindings(self, wnd):
		BaseDialog._create_bindings(self, wnd)
		wnd.Bind(wx.EVT_BUTTON, self._on_save, id=wx.ID_SAVE)
		wnd.Bind(wx.EVT_BUTTON, self._on_btn_file_select,
				self['btn_filen_select'])
		wnd.Bind(wx.EVT_RADIOBUTTON, self._on_format_change,
				self['rb_format_txt'])
		wnd.Bind(wx.EVT_RADIOBUTTON, self._on_format_change,
				self['rb_format_csv'])

	def _setup(self):
		self['tc_filename'].SetValidator(Validator(
				validators=LVALID.NotEmptyValidator(), field='filename'))

	def _on_save(self, evt):
		if not self._wnd.Validate():
			return
		if not self._wnd.TransferDataFromWindow():
			return
		details = 0
		if self['rb_details_normal'].GetValue():
			details = 1
		elif self['rb_details_verbose'].GetValue():
			details = 2
		filename = self['tc_filename'].GetValue()
		with open(filename, 'wt') as dfile:
			if self['rb_format_txt'].GetValue():  # txt
				exporter.dump_tasks_to_text(self._tasks, details, output=dfile)
			else:  # csv
				exporter.dump_tasks_to_csv(self._tasks, details, output=dfile)
		dlg = wx.MessageDialog(self._wnd, _("Export complete."), _("Export"),
				wx.OK)
		dlg.ShowModal()
		dlg.Destroy()

	def _on_btn_file_select(self, _evt):
		default_dir = os.path.expanduser("~")
		default_file = ("tasks.txt" if self['rb_format_txt'].GetValue() else
				'tasks.csv')
		curr_filename = self['tc_filename'].GetValue()
		if curr_filename:
			default_file = os.path.basename(curr_filename)
			default_dir = os.path.dirname(curr_filename)
		dlg = wx.FileDialog(self._wnd,
				_("Please select target file."),
				defaultDir=default_dir, defaultFile=default_file,
				style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
		if dlg.ShowModal() == wx.ID_OK:
			self['tc_filename'].SetValue(dlg.GetPath())
		dlg.Destroy()

	def _on_format_change(self, _evt):
		filename = self['tc_filename'].GetValue()
		if filename:
			fname, fext = os.path.splitext(filename)
			if self['rb_format_txt'].GetValue():
				if fext.lower() == '.csv':
					self['tc_filename'].SetValue(fname + ".txt")
			else:
				if fext.lower() != '.csv':
					self['tc_filename'].SetValue(fname + ".csv")
