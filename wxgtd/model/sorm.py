# -*- coding: utf-8 -*-

"""
Prosty ORM
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2009-2013"
__version__ = "2011-05-15"


import logging
import sqlite3
import locale
import itertools

_LOG = logging.getLogger(__name__)


class _Singleton(object):
	def __new__(cls, *args, **kwarg):
		instance = cls.__dict__.get('__instance__')
		if instance is None:
			instance = object.__new__(cls)
			instance._init(*args, **kwarg)
			cls.__instance__ = instance
		return instance

	def _init(self, *args, **kwarg):
		pass


class _CursorWrapper(object):
	"""Wrapper for sqlite3.Cursor that close cursor after leave context"""
	def __init__(self, connection):
		self._connection = connection
		self._cursor = None

	def __enter__(self):
		self._cursor = self._connection.cursor()
		return self._cursor

	def __exit__(self, type_=None, value=None, traceback=None):
		self._cursor.close()


class DbConnection(_Singleton):
	""" Singleton for all db connections """
	def _init(self):
		self._connection = None

	def open(self, *args, **kwargs):
		""" Open connection """
		_LOG.debug('DbConnection.open(%r, %r)', args, kwargs)
		self.close()
		self._connection = sqlite3.connect(*args, **kwargs)
		self._connection.row_factory = sqlite3.Row
		self._connection.create_collation('localecoll', locale.strcoll)

	def close(self):
		""" Close current connection """
		if self._connection:
			_LOG.debug('DbConnection.close()')
			self._connection.close()
			self._connection = None

	def get_cursor(self):
		""" Return _CursorWrapper for current connection"""
		if self._connection:
			return _CursorWrapper(self._connection)
		_LOG.error("DbConnection.get_cursor ERROR: not connected")

	def get_raw_cursor(self):
		""" Get sqlite3.Cursor for current connection """
		if self._connection:
			return self._connection.cursor()
		_LOG.error("DbConnection.get_raw_cursor ERROR: not connected")

	def execue(self, *args, **kwargs):
		""" Execute query """
		_LOG.debug('DbConnection.execute(%r, %r)', args, kwargs)
		if self._connection:
			with self.get_cursor() as curs:
				curs.execute(*args, **kwargs)
		_LOG.error("DbConnection.execute ERROR: not connected")


class Model(object):
	"""docstring for Model"""

	_table_name = None
	_fields = {}  # map class property -> db field (optional)
	_primary_keys = []  # list of primary keys properties

	def __init__(self, **kwargs):
		super(Model, self).__init__()
		for key in self._fields.keys():
			setattr(self, key, None)
		for key, val in kwargs.iteritems():
			if key in self._fields:
				setattr(self, key, val)

	def __str__(self):
		res = ['<', self.__class__.__name__,
				'TABLE=%r' % self._table_name]
		res.extend('%r=%r' % (key, val) for key, val
				in self.__dict__.iteritems()
				if key[0] != '_')
		res.append('>')
		return ' '.join(res)

	@classmethod
	def select(cls, order=None, limit=None, offset=None, distinct=None,
				where_stmt=None, group_by=None, **where):
		"""Select object according to given params """
		sql, query_params = cls._create_select_query(order, limit, offset,
				distinct, where_stmt, group_by, **where)
		with DbConnection().get_cursor() as cursor:
			cursor.execute(sql, query_params)
			for row in cursor:
				yield cls(**row)

	@classmethod
	def get(cls, **where):
		"""Get one object"""
		result = list(cls.select(limit=1, **where))
		if result:
			return result[0]
		return None

	@classmethod
	def all(cls):
		"""Select all object."""
		return cls.select()

	def save(self):
		"""Save (insert) current object as new record."""
		sql, query_params = self._create_save_stmt()
		_LOG.debug("%s._save_new_object sql=%r params=%r",
				self.__class__.__name__, sql,
				query_params)
		with DbConnection().get_cursor() as cursor:
			cursor.execute(sql, query_params)

	def update(self):
		"""Update current object.
			NOTE: this use primary key for select updated obj.
		"""
		sql, query_params = self._create_update_stmt()
		_LOG.debug("%s._update_object sql=%r params=%r",
				self.__class__.__name__, sql, query_params)
		with DbConnection().get_cursor() as cursor:
			cursor.execute(sql, query_params)

	def delete(self):
		"""Delete current object.
			NOTE: valid primary key is required.
		"""
		sql, query_params = self._create_delete_stmt()
		_LOG.debug("%s._update_object sql=%r params=%r",
				self.__class__.__name__, sql, query_params)
		with DbConnection().get_cursor() as cursor:
			cursor.execute(sql, query_params)

	@classmethod
	def _create_select_query(cls, order=None, limit=None, offset=None,
				distinct=None, where_stmt=None, group_by=None, **where):
		"""Prepare select query for given parameters """
		sqls = ['SELECT', ("DISTINCT" if distinct else "")]
		# use "AS" if object fiels is diferrent from table column
		sqls.append(', '.join(((field + " AS " + key)
				if (field and field != key) else key)
				for key, field in cls._fields.iteritems()))
		sqls.append('FROM "%s"' % cls._table_name)
		query_params = []
		if where_stmt or where_stmt:
			sqls.append('WHERE')
			where_params = []
			if where_stmt:
				where_params.append(where_stmt)
			if where:
				for column, value in where.iteritems():
					where_params.append("%s=?" % (cls._fields[column] or column))
					query_params.append(value)
			sqls.append(' AND '.join(where_params))
		if group_by:
			sqls.append("GROUP BY %s" % group_by)
		if order:
			sqls.append('ORDER BY %s' % order)
		if limit:
			sqls.append('LIMIT %d' % limit)
		if offset:
			sqls.append('OFFSET %d' % offset)
		sql = ' '.join(sqls)
		_LOG.debug("Query.select sql=%r", sql)
		return sql, query_params

	def _create_update_stmt(self):
		"""Prepare sql stmt and parameters for update current object."""
		assert bool(self._primary_keys)
		values = [((field or key), getattr(self, key))
				for key, field in self._fields.iteritems()
				if key not in self._primary_keys]
		pkeys = [(self._fields[key] or key, getattr(self, key))
				for key in self._primary_keys]
		sql = ['UPDATE', self._table_name, 'SET']
		sql.append(', '.join(val[0] + "=?" for val in values))
		sql.append('WHERE')
		sql.append(' AND '.join(val[0] + "=?" for val in pkeys))
		sql = ' '.join(sql)
		query_params = [val[1] for val in itertools.chain(values, pkeys)]
		return sql, query_params

	def _create_save_stmt(self):
		"""Prepare sql for save (insert) new object"""
		values = [(field or key, getattr(self, key)) for key, field
				in self._fields.iteritems()]
		sql = ['INSERT INTO', self._table_name, '(']
		sql.append(', '.join(val[0] for val in values))
		sql.append(') VALUES (')
		sql.append(', '.join(['?'] * len(values)))
		sql.append(')')
		sql = ' '.join(sql)
		query_params = [val[1] for val in values]
		return sql, query_params

	def _create_delete_stmt(self):
		"""Prepare sql for delete object"""
		assert bool(self._primary_keys)
		pkeys = [(self._fields[key] or key, getattr(self, key))
				for key in self._primary_keys]
		sql = ['DELETE FROM', self._table_name, 'WHERE']
		sql.append(' AND '.join(val[0] + "=?" for val in pkeys))
		sql = ' '.join(sql)
		query_params = [val[1] for val in pkeys]
		return sql, query_params
