# -*- coding: utf-8 -*-
""" Setup dropbox account dialog.

Copyright (c) Karol Będkowski, 2013

This file is part of wxGTD
Licence: GPLv2+
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2013"
__version__ = "2013-06-29"

import logging
import gettext

import wx
try:
	import dropbox
except ImportError:
	dropbox = None  # pylint: disable=C0103

from wxgtd.wxtools.validators import Validator
from wxgtd.wxtools.validators import v_length as LVALID
from wxgtd.lib.appconfig import AppConfigWrapper

from wxgtd.gui import message_boxes as msg
from ._base_dialog import BaseDialog

_ = gettext.gettext
_LOG = logging.getLogger(__name__)


class DlgDropboxAuth(BaseDialog):
	""" Configure Dropbox account authorization.

	Args:
		parent: parent window
	"""

	def __init__(self, parent):
		BaseDialog.__init__(self, parent, 'dlg_dropbox_auth')
		self._setup()

	def _create_bindings(self, wnd):
		BaseDialog._create_bindings(self, wnd)
		wnd.Bind(wx.EVT_BUTTON, self._on_ok, self['btn_auth'])
		wnd.Bind(wx.EVT_BUTTON, self._on_btn_app_console, self['btn_app_console'])

	def _setup(self):
		self._config = config = AppConfigWrapper()
		self['tc_app_key'].SetValidator(Validator(config, 'dropbox/appkey',
			validators=LVALID.NotEmptyValidator(),
			field=_("app key")))
		self['tc_app_secret'].SetValidator(Validator(config,
			'dropbox/appsecret', validators=LVALID.NotEmptyValidator(),
			field=_("app secret")))

	def _on_ok(self, _evt):
		if not self._wnd.Validate():
			return
		if not self._wnd.TransferDataFromWindow():
			return
		if not self._auth():
			return
		self._wnd.EndModal(wx.ID_OK)

	def _on_btn_app_console(self, _evt):  # pylint: disable=R0201
		wx.LaunchDefaultBrowser('https://www.dropbox.com/developers/apps/create')

	def _auth(self):
		if dropbox is None:
			return False
		sess = dropbox.session.DropboxSession(
				self._appconfig.get('dropbox', 'appkey'),
				self._appconfig.get('dropbox', 'appsecret'), 'dropbox')
		request_token = sess.obtain_request_token()
		while True:
			try:
				access_token = sess.obtain_access_token(request_token)
				_LOG.debug(access_token)
			except dropbox.rest.ErrorResponse as error:
				_LOG.info('_auth error: %r', error)
				url = sess.build_authorize_url(request_token)
				wx.LaunchDefaultBrowser(url)
				if not msg.message_box_question(self._wnd,
						_("Allow wxGTD to access Dropbox files"),
						_("Please authorize application in Dropbox.")):
					return False
			else:
				self._appconfig.set('dropbox', 'oauth_key', access_token.key)
				self._appconfig.set('dropbox', 'oauth_secret', access_token.secret)
				db_client = dropbox.client.DropboxClient(sess)
				self._appconfig.set('dropbox', 'info',
						db_client.account_info()["display_name"])
				return bool(db_client)
