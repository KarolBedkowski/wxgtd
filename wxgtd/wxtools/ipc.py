#!/usr/bin/python
# -*- coding: utf-8 -*-
# pylint: disable-msg=R0901, R0904
""" wxShell (pyCrust)

Copyright (c) Karol Będkowski, 2004-2013

This file is part of kPyLibs

This is free software; you can redistribute it and/or modify it under the
terms of the GNU General Public License as published by the Free Software
Foundation, version 2.
"""

__author__ = 'Karol Będkowski'
__copyright__ = 'Copyright (C) Karol Będkowski 2006-2013'
__version__ = "2013-04-27"


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

try:
	from wx.lib.pubsub.pub import Publisher
except ImportError:
	from wx.lib.pubsub import Publisher  # pylint: disable=E0611

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
			Publisher().sendMessage(message, data=data_j.get("data"))
			self.request.sendall("ok")
		except Exception as err:
			print err


class _ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
	pass


class IPCServer:

	def __init__(self):
		self.server = None

	def start(self):
		# Port 0 means to select an arbitrary unused port
		HOST, PORT = "localhost", 0
		self.server = server = _ThreadedTCPServer((HOST, PORT),
				_ThreadedTCPRequestHandler)
		ip, port = server.server_address
		self.server_thread = server_thread = threading.Thread(
				target=server.serve_forever)
		server_thread.daemon = True
		server_thread.start()
		_LOG.info("IPCServer.started(port=%r)", port)
		return port

	def stop(self):
		self.server.shutdown()


def send(port, message, data=None):
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


def check_lock(lock_path, message="check"):
	if os.path.isfile(lock_path):
		# lock file exists
		_LOG.debug("check_lock: file exists %s", lock_path)
		with open(lock_path)as lock_file:
			try:
				port = int(lock_file.read())
				_LOG.debug("check_lock: port %r", port)
				if 1024 < port < 65536:
					resp = send(port, message)
					_LOG.debug("check_lock: check send; res=%r", resp)
					if resp == "ok":
						return port
			except:
				pass
		# death lock file
		remove_lock(lock_path)
	return None


def create_lock(lock_path, port):
	try:
		with open(lock_path, "w") as lock_file:
			lock_file.write(str(port))
	except OSError:
		_LOG.exception("create_lock error (%r, %r)", lock_path, port)
		return False
	return True


def remove_lock(lock_path):
	try:
		os.unlink(lock_path)
	except OSError:
		_LOG.exception("remove_lock error (%r)", lock_path)
		return False
	return True
