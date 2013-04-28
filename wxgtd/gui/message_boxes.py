#!/usr/bin/python
# -*- coding: utf-8 -*-
""" Various message boxes definition.

Copyright (c) Karol Będkowski, 2004-2013

This file is part of KPyLibs

This is free software; you can redistribute it and/or modify it under the
terms of the GNU General Public License as published by the Free Software
Foundation, version 2.
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2004-2013"
__version__ = "2013-04-28"
__all__ = ['message_box_error', 'message_box_info',
		'message_box_question_yesno', 'message_box_warning_yesno',
		'message_box_warning_yesnocancel', 'message_box_not_save_confirm',
		'message_box_error_ex', 'message_box_info_ex', 'message_box_delete_confirm',
		'message_box_question']

import gettext

import wx

_ = gettext.gettext


class MyMessageDialog(wx.Dialog):
	""" Custom message box dialog.

	Args:
		parent: parent window
		primary_text: primary text showed in dialog
		secondary_text: optional additional text to show
		buttons: buttons ids to create
		icon: icon to show in dialog.
	"""

	def __init__(self, parent, primary_text, secondary_text, buttons=None,
			icon=None):
		wx.Dialog.__init__(self, parent, -1, '')
		sizer = wx.BoxSizer(wx.VERTICAL)

		sizer_inner = wx.BoxSizer(wx.HORIZONTAL)

		if icon:
			bmp = wx.ArtProvider.GetBitmap(icon, wx.ART_MESSAGE_BOX)
			sizer_inner.Add(wx.StaticBitmap(self, -1, bmp), 0, wx.EXPAND)
			sizer_inner.Add((12, 12))

		sizer_text = wx.BoxSizer(wx.VERTICAL)

		if primary_text and secondary_text:
			fstyle = wx.SystemSettings_GetFont(wx.SYS_DEFAULT_GUI_FONT)
			fstyle.SetWeight(wx.FONTWEIGHT_BOLD)
			fstyle.SetPointSize(fstyle.GetPointSize() + 2)
			ptext = wx.StaticText(self, -1, primary_text)
			ptext.SetFont(fstyle)
			sizer_text.Add(ptext, 0, wx.EXPAND)
			sizer_text.Add((12, 12))
		elif not secondary_text:
			ptext = wx.StaticText(self, -1, primary_text)
			sizer_text.Add(ptext, 0, wx.EXPAND)

		if secondary_text:
			ptext = wx.StaticText(self, -1, secondary_text)
			sizer_text.Add(ptext, 0, wx.EXPAND)

		sizer_inner.Add(sizer_text, 0)
		sizer.Add(sizer_inner, 0, wx.EXPAND | wx.ALL, 12)

		buttons_grid = self._create_buttons(buttons)
		sizer.Add(buttons_grid, 0, wx.EXPAND | wx.ALL, 12)
		self.SetSizerAndFit(sizer)

		self.Bind(wx.EVT_BUTTON, self._on_btn_no, id=wx.ID_NO)
		self.Bind(wx.EVT_BUTTON, self._on_btn_yes, id=wx.ID_YES)
		self.Bind(wx.EVT_BUTTON, self._on_btn_save, id=wx.ID_SAVE)

	def _on_btn_no(self, _evt):
		self.EndModal(wx.ID_NO)

	def _on_btn_yes(self, _evt):
		self.EndModal(wx.ID_YES)

	def _on_btn_save(self, _evt):
		self.EndModal(wx.ID_SAVE)

	def _create_buttons(self, buttons):
		return self.CreateStdDialogButtonSizer(buttons or wx.ID_OK)


class DialogConfirmSave(MyMessageDialog):
	""" Confirm save dialog. """

	def __init__(self, parent, doc_name, time_period=None, saveas=False):
		if doc_name:
			primary_text = _("Save the changes to\n%(doc_name)s before closing?") \
					% dict(doc_name=doc_name)
		else:
			primary_text = _("Save the changes before closing?")
		if time_period is None:
			secondary_text = _('If you close without saving, changes will be discarded')
		else:
			secondary_text = _('If you close without saving, changes from the last\n'
				'%(time)s will be discarded''') % dict(time=time_period)
		self.saveas = saveas
		MyMessageDialog.__init__(self, parent, primary_text, secondary_text, None,
				wx.ART_WARNING)

	def _create_buttons(self, buttons):
		grid = wx.StdDialogButtonSizer()
		btn = wx.Button(self, wx.ID_NO, _('Close &without Saving'))
		grid.AddButton(btn)
		btn = wx.Button(self, wx.ID_CANCEL)
		grid.AddButton(btn)
		btn_save_text = _('Save &As') if self.saveas else _('Save')
		btn = wx.Button(self, wx.ID_YES, btn_save_text)
		btn.SetDefault()
		grid.AddButton(btn)
		grid.Realize()
		return grid


class DialogSimpleConfirmSave(MyMessageDialog):
	""" Simple confirm save dialog. """
	def __init__(self, parent, primary_text, secondary_text=None):
		MyMessageDialog.__init__(self, parent, primary_text, secondary_text, None,
				wx.ART_WARNING)

	def _create_buttons(self, buttons):
		grid = wx.StdDialogButtonSizer()
		btn = wx.Button(self, wx.ID_NO)
		grid.AddButton(btn)
		btn = wx.Button(self, wx.ID_SAVE)
		grid.AddButton(btn)
		grid.Realize()
		btn.SetDefault()
		return grid


class DialogConfirmDelete(MyMessageDialog):
	""" Confirm delete dialog. """

	def __init__(self, parent, name, secondary_text=None):
		primary_text = _("Delete %s?") % name
		secondary_text = secondary_text or \
				_('After removal, it cannot be recovered.')
		MyMessageDialog.__init__(self, parent, primary_text, secondary_text, None,
				wx.ART_QUESTION)

	def _create_buttons(self, buttons):
		grid = wx.StdDialogButtonSizer()
		btn = wx.Button(self, wx.ID_CANCEL)
		grid.AddButton(btn)
		btn = wx.Button(self, wx.ID_YES, _("Delete"))
		btn.SetDefault()
		grid.AddButton(btn)
		grid.Realize()
		return grid


class DialogQuestion(MyMessageDialog):
	""" Question dialog. """

	def __init__(self, parent, primary_text, secondary_text, affirmative_button,
			cancel_button):
		self.affirmative_button = affirmative_button
		self.cancel_button = cancel_button
		MyMessageDialog.__init__(self, parent, primary_text, secondary_text, None,
				wx.ART_QUESTION)

	def _create_buttons(self, buttons):
		grid = wx.StdDialogButtonSizer()
		btn = wx.Button(self, wx.ID_CANCEL, self.cancel_button)
		grid.AddButton(btn)
		btn = wx.Button(self, wx.ID_YES, self.affirmative_button)
		btn.SetDefault()
		grid.AddButton(btn)
		grid.Realize()
		return grid


def message_box_error(parent, msg, title=''):
	""" Display error message dialog.

	Args:
		parent: parent window
		message: message to show
		title: dialog title
	"""
	dlg = wx.MessageDialog(parent, str(msg), title,
			wx.OK | wx.CENTRE | wx.ICON_ERROR)
	dlg.ShowModal()
	dlg.Destroy()


def message_box_error_ex(parent, header, message):
	""" Display extended error message dialog.

	Args:
		parent: parent window
		header: header displayed in dialog.
		message: message to show
	"""
	dlg = MyMessageDialog(parent, header, message, wx.OK, wx.ART_ERROR)
	dlg.ShowModal()
	dlg.Destroy()


def message_box_info(parent, msg, title=''):
	""" Display info message dialog.

	Args:
		parent: parent window
		message: message to show
		title: dialog title
	"""
	dlg = wx.MessageDialog(parent, str(msg), title,
			wx.OK | wx.CENTRE | wx.ICON_INFORMATION)
	dlg.ShowModal()
	dlg.Destroy()


def message_box_info_ex(parent, header, message):
	""" Display extended info message dialog.

	Args:
		parent: parent window
		header: header displayed in dialog.
		message: message to show
	"""
	dlg = MyMessageDialog(parent, header, message, wx.OK, wx.ART_INFORMATION)
	dlg.ShowModal()
	dlg.Destroy()


def message_box_question_yesno(parent, msg, title=''):
	""" Display question dialog with yes/no buttons.

	Args:
		parent: parent window
		message: message to show
		title: optional dialog title

	Returns:
		true if user click YES
	"""
	dlg = wx.MessageDialog(parent, msg, title,
			wx.YES_NO | wx.NO_DEFAULT | wx.CENTRE | wx.ICON_QUESTION)
	res = dlg.ShowModal()
	dlg.Destroy()
	return res == wx.ID_YES


def message_box_warning_yesno(parent, msg, title=''):
	""" Display warning dialog with yes/no buttons.

	Args:
		parent: parent window
		message: message to show
		title: optional dialog title

	Returns:
		true if user click YES
	"""
	dlg = wx.MessageDialog(parent, msg, title,
			wx.YES_NO | wx.NO_DEFAULT | wx.CENTRE | wx.ICON_WARNING)
	res = dlg.ShowModal()
	dlg.Destroy()
	return res == wx.ID_YES


def message_box_warning_yesnocancel(parent, msg, title=''):
	""" Display warning dialog with yes/no/cancel button..

	Args:
		parent: parent window
		message: message to show
		title: optional dialog title

	Returns:
		Id clicked button.
	"""
	dlg = wx.MessageDialog(parent, msg, title,
			wx.YES_NO | wx.CANCEL | wx.YES_DEFAULT | wx.CENTRE | wx.ICON_WARNING)
	res = dlg.ShowModal()
	dlg.Destroy()
	return res


def message_box_not_save_confirm(parent, doc_name, time_period=None,
		saveas=False):
	""" Display confirm save dialog..

	Args:
		parent: parent window
		doc_name: what is not saved
		time_period: time from last save
		saveas: show "Save as" button instead of "Save".

	Returns:
		Id clicked button.
	"""
	dlg = DialogConfirmSave(parent, doc_name, time_period, saveas)
	res = dlg.ShowModal()
	dlg.Destroy()
	return res


def message_box_save_confirm(parent, primary_text, secondary_text=None):
	""" Display simple confirm save dialog..

	Args:
		parent: parent window
		primary_text: main text to show
		secondary_text: optional additional information to show

	Returns:
		true if user click save.
	"""
	dlg = DialogSimpleConfirmSave(parent, primary_text, secondary_text)
	res = dlg.ShowModal()
	dlg.Destroy()
	return res == wx.ID_SAVE


def message_box_delete_confirm(parent, name, secondary_text=None):
	""" Display simple delete dialog.

	Args:
		parent: parent window
		primary_text: main text to show
		secondary_text: optional additional information to show

	Returns:
		true if user click yes.
	"""
	dlg = DialogConfirmDelete(parent, name, secondary_text)
	res = dlg.ShowModal()
	dlg.Destroy()
	return res == wx.ID_YES


def message_box_question(parent, primary_text, secondary_text,
		affirmative_button=None, cancel_button=None):
	""" Display simple confirm dialog.

	Args:
		parent: parent window
		primary_text: main text to show
		secondary_text: optional additional information to show
		affirmative_button: positive button id
		cancel_button: negative button id

	Returns:
		true if user click yes.
	"""
	affirmative_button = affirmative_button or _('Ok')
	cancel_button = cancel_button or _("Cancel")
	dlg = DialogQuestion(parent, primary_text, secondary_text, affirmative_button,
			cancel_button)
	res = dlg.ShowModal()
	dlg.Destroy()
	return res == wx.ID_YES
