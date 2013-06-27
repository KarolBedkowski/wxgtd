# -*- coding: utf-8 -*-
""" Preferences dialog.

Copyright (c) Karol Będkowski, 2013

This file is part of wxGTD
Licence: GPLv2+
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2013"
__version__ = "2013-04-28"

import os
import logging
import gettext

import wx

from wxgtd.wxtools.validators import Validator, ValidatorDv
from wxgtd.model import enums
from wxgtd.lib.appconfig import AppConfig
from wxgtd.wxtools import wxutils

from ._base_dialog import BaseDialog
from .dlg_remind_settings import DlgRemindSettings
from .dlg_show_settings import DlgShowSettings

_LOG = logging.getLogger(__name__)
_ = gettext.gettext


class AppConfigWrapper(object):
	""" Wrapper for AppConfig class that allow use it with validators. """
	# pylint: disable=R0903

	def __init__(self):
		self._config = AppConfig()

	def __getitem__(self, key):
		key = key.split('/')
		return self._config.get(key[0], key[1])

	def __setitem__(self, key, value):
		key = key.split('/')
		self._config.set(key[0], key[1], value)

	def get(self, key, default=None):
		key = key.split('/')
		return self._config.get(key[0], key[1], default)


class DlgPreferences(BaseDialog):
	""" Preferences dialog.

	Args:
		parent: parent window
	"""

	def __init__(self, parent):
		BaseDialog.__init__(self, parent, 'dlg_preferences', save_pos=False)
		self._setup_comboboxes()
		self._setup()
		self._refresh_labels()

	def _create_bindings(self, wnd):
		BaseDialog._create_bindings(self, wnd)
		self['sl_hotlist_priority'].Bind(wx.EVT_SCROLL, self._on_sl_priority)
		self['btn_sync_file_select'].Bind(wx.EVT_BUTTON,
				self._on_btn_sync_file_select)
		self['sl_task_def_priority'].Bind(wx.EVT_SCROLL,
				self._on_sl_task_def_priority)
		self['btn_task_def_remind_set'].Bind(wx.EVT_BUTTON,
				self._on_btn_task_def_remind_set)
		self['btn_task_def_hide_until_set'].Bind(wx.EVT_BUTTON,
				self._on_btn_task_def_hide_set)

	def _setup(self):  # pylint: disable=R0201
		_LOG.debug("DlgPreferences()")
		config = self._config = AppConfigWrapper()

		self['sc_hotlist_due'].SetValidator(Validator(config, 'hotlist/due'))
		self['sl_hotlist_priority'].SetValidator(Validator(config,
				'hotlist/priority'))
		self['cb_hotlist_starred'].SetValidator(Validator(config,
				'hotlist/starred'))
		self['cb_hotlist_next_action'].SetValidator(Validator(config,
				'hotlist/next_action'))
		self['cb_hotlist_started'].SetValidator(Validator(config,
				'hotlist/starred'))
		self['cb_hotlist_started'].SetValidator(Validator(config,
				'hotlist/started'))
		self['tc_sync_filename'].SetValidator(Validator(config,
				'files/last_sync_file'))
		self._on_sl_priority(None)
		self['cb_sync_on_startup'].SetValidator(Validator(config,
				'sync/sync_on_startup'))
		self['cb_sync_on_exit'].SetValidator(Validator(config,
				'sync/sync_on_exit'))
		cond_or = config.get('hotlist/condition_or', True)
		self['rb_hotlist_cond_or'].SetValue(cond_or)
		self['rb_hotlist_cond_and'].SetValue(not cond_or)
		# task
		# # inheritance from project
		self['cb_tasks_inh_context'].SetValidator(Validator(config,
				'task/inherit_context'))
		self['cb_tasks_inh_goal'].SetValidator(Validator(config,
				'task/inherit_goal'))
		self['cb_tasks_inh_folder'].SetValidator(Validator(config,
				'task/inherit_folder'))
		self['cb_tasks_inh_tags'].SetValidator(Validator(config,
				'task/inherit_tags'))
		# # defaults
		self['cb_task_def_status'].SetValidator(ValidatorDv(config,
				'task/default_status'))
		self['sl_task_def_priority'].SetValidator(Validator(config,
				'task/default_priority'))
		# notification
		self['cb_notif_popup_reminds'].SetValidator(Validator(config,
				'notification/popup_alarms'))
		# gui
		self['cb_gui_hide_on_start'].SetValidator(Validator(config,
				'gui/hide_on_start'))
		self['cb_gui_min_to_tray'].SetValidator(Validator(config,
				'gui/min_to_tray'))
		self['cb_gui_confirm_complete_dlg'].SetValidator(Validator(config,
				'gui/confirm_complete_dlg'))

	def _setup_comboboxes(self):
		cb_status = self['cb_task_def_status']
		cb_status.Clear()
		for key, status in sorted(enums.STATUSES.iteritems()):
			cb_status.Append(status, key)

	def _on_ok(self, evt):
		if not self._wnd.Validate():
			return
		if not self._wnd.TransferDataFromWindow():
			return
		self._config['hotlist/condition_or'] = \
				self['rb_hotlist_cond_or'].GetValue()
		BaseDialog._on_ok(self, evt)

	def _on_sl_priority(self, _evt):
		self['l_hotlist_priority'].SetLabel(
				enums.PRIORITIES[self['sl_hotlist_priority'].GetValue()])

	def _on_sl_task_def_priority(self, _evt):
		self['l_task_def_prio'].SetLabel(
				enums.PRIORITIES[self['sl_task_def_priority'].GetValue()])

	def _on_btn_sync_file_select(self, _evt):
		last_file = self['tc_sync_filename'].GetValue()
		if not last_file:
			last_file = os.path.expanduser('~/')
		dlg = wx.FileDialog(self._wnd,
				_("Please select sync file."),
				defaultDir=os.path.dirname(last_file),
				defaultFile=last_file,
				style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
		if dlg.ShowModal() == wx.ID_OK:
			self['tc_sync_filename'].SetValue(dlg.GetPath())
		dlg.Destroy()

	def _on_btn_task_def_remind_set(self, _evt):
		dlg = DlgRemindSettings(self._wnd, None,
				self._appconfig.get('task', 'default_remind', ''),
				no_date=True)
		if dlg.run(True):
			self._appconfig.set('task', 'default_remind', dlg.alarm_pattern)
			self._refresh_labels()

	def _on_btn_task_def_hide_set(self, _evt):
		dlg = DlgShowSettings(self._wnd, None, self._appconfig.get('task',
			'default_hide', ''), no_date=True)
		if dlg.run(True):
			self._appconfig.set('task', 'default_hide', dlg.pattern)
			self._refresh_labels()

	@wxutils.call_after
	def _refresh_labels(self):
		self['l_task_def_prio'].SetLabel(
				enums.PRIORITIES[self['sl_task_def_priority'].GetValue()])
		self['l_task_def_remind'].SetLabel(
				enums.REMIND_PATTERNS.get(self._appconfig.get('task',
					'default_remind', ""), ""))
		self['l_task_def_hide_until'].SetLabel(
				enums.HIDE_PATTERNS.get(self._appconfig.get('task',
					'default_hide', ""), ""))
