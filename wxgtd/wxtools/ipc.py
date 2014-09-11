#!/usr/bin/python
# -*- coding: utf-8 -*-
# pylint: disable-msg=R0901, R0904
""" Inter process communication.

Copyright (c) Karol Będkowski, 2013

This file is part of wxGTD

This is free software; you can redistribute it and/or modify it under the
terms of the GNU General Public License as published by the Free Software
Foundation, version 2.
"""

__author__ = 'Karol Będkowski'
__copyright__ = 'Copyright (C) Karol Będkowski 2013'
__version__ = "2013-07-11"


import os
import logging
import threading
import socket
import SocketServer
try:
	import cjson
	_JSON_DECODER = cjson.decode
	_JSON_ENCODER = cjson.encode
except ImportError:
	import json
	_JSON_DECODER = json.loads
	_JSON_ENCODER = json.dumps


from wxgtd.wxtools.wxpub import publisher

_LOG = logging.getLogger(__name__)


class _ThreadedTCPRequestHandler(SocketServer.BaseRequestHandler):

	def handle(self):
		data = self.request.recv(1024).strip()
		_LOG.info("_ThreadedTCPRequestHandler.handle(%r)", data)
		try:
			if data == "check":
				self.request.sendall("ok")
				return
			data_j = _JSON_DECODER(data.decode("UTF-8"))
			message = data_j['message']
			publisher.sendMessage(message, data=data_j.get("data"))
			self.request.sendall("ok")
		except Exception as err:  # pylint: disable=W0703
			print err


class _ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
	pass


class IPC:
	""" Inter process communication controller.

	Args:
		lock_path: path to file holding local server port.
	"""

	def __init__(self, lock_path):
		self._server = None
		self._server_thread = None
		self.lock_path = lock_path
		self.port = None

	def startup(self, message=None):
		""" Check is another app is runing; run ipc server if not.
		Args:
			message: message to sent for check.
		Returns:
			False = app exists and responding.
		"""
		if self.check_lock(message) is not None:
			return False
		return self.start()

	def start(self):
		""" Start IPC server. """
		self._server = server = _ThreadedTCPServer(("localhost", 0),
				_ThreadedTCPRequestHandler)
		addr_ip, port = server.server_address
		self._server_thread = server_thread = threading.Thread(
				target=server.serve_forever)
		server_thread.daemon = True
		server_thread.start()
		_LOG.info("IPC.started(port=%r, ip=%r)", port, addr_ip)
		self.port = port
		return self._create_lock()

	def shutdown(self):
		""" Shutdown server. """
		self._server.shutdown()
		self._remove_lock()

	def check_lock(self, message=None):
		""" Check lock file; if exists - checking is app response.

		Args:
			message: message to sent for check.
		"""
		if os.path.isfile(self.lock_path):
			# lock file exists
			_LOG.debug("check_lock: file exists %s", self.lock_path)
			with open(self.lock_path)as lock_file:
				try:
					port = int(lock_file.read())
					_LOG.debug("check_lock: port %r", port)
					if 1024 < port < 65536:
						resp = self.send(message or "check", port=port)
						_LOG.info("check_lock: check send; res=%r", resp)
						if resp == "ok":
							return port
				except:  # pylint: disable=W0702
					pass
			# death lock file
			self._remove_lock()
		return None

	def _create_lock(self):
		_LOG.info("IPC._create_lock: %r -> %r", self.lock_path, self.port)
		try:
			with open(self.lock_path, "w") as lock_file:
				lock_file.write(str(self.port))
		except OSError:
			_LOG.exception("create_lock error (%r, %r)", self.lock_path,
					self.port)
			return False
		return True

	def _remove_lock(self):
		try:
			os.unlink(self.lock_path)
		except OSError:
			_LOG.exception("_remove_lock error (%r)", self.lock_path)
			return False
		return True

	def send(self, message, data=None, port=None):
		""" Send message to running application.

		Args:
			message: message to send
			data: optional data to send
			port: optional destination port.
		Returns:
			Server response
		"""
		port = port or self.port
		_LOG.info("send(%r, %r, %r)", port, message, data)
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sock.connect(("localhost", port))
		try:
			data_j = _JSON_ENCODER({'message': message, 'data': data})
			sock.sendall(data_j)
			response = sock.recv(1024)
			return response
		finally:
			sock.close()
		return None
