# -*- coding: utf-8 -*-

"""
very Simple ORM

TODO: default sort col
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2013"
__version__ = "2013-03-05"


import logging
import sqlite3
import locale
import itertools
#import types
import functools
import time

_LOG = logging.getLogger(__name__)


def cached(ttl=60):
	""" Decorator for cache function results.

	import time

	@cache(tty=1)
	def rand(
	"""

	def cache(obj):
		cache = obj.cache = {}

		@functools.wraps(obj)
		def cacher(*args, **kwargs):
			if '__NO_CACHE__' in kwargs:
				kwargs.pop('__NO_CACHE__')
				return obj(*args, **kwargs)
			params = hash((args, repr(kwargs)))
			now = time.time()
			if params in cache:
				last_update, value = cache[params]
				if now - last_update < ttl:
					return value
			value = obj(*args, **kwargs)
			cache[params] = now, value
			return value
		return cacher
	return cache


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


class DbConnection(object):
	""" Singleton for all db connections """

	_instance = None

	def __new__(cls, *args, **kwarg):
		if cls._instance is None:
			cls._instance = object.__new__(cls)
			cls._instance._init(*args, **kwarg)
		return cls._instance

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
		raise RuntimeError('Not connected')

	def get_raw_cursor(self):
		""" Get sqlite3.Cursor for current connection """
		if self._connection:
			return self._connection.cursor()
		_LOG.error("DbConnection.get_raw_cursor ERROR: not connected")
		raise RuntimeError('Not connected')

	def execue(self, *args, **kwargs):
		""" Execute query """
		_LOG.debug('DbConnection.execute(%r, %r)', args, kwargs)
		if self._connection:
			with self.get_cursor() as curs:
				curs.execute(*args, **kwargs)
		else:
			_LOG.error("DbConnection.execute ERROR: not connected")
			raise RuntimeError('Not connected')

	def execuescript(self, *args, **kwargs):
		""" Execute query """
		_LOG.debug('DbConnection.executescript(%r, %r)', args, kwargs)
		if self._connection:
			with self.get_cursor() as curs:
				curs.executescript(*args, **kwargs)
		else:
			_LOG.error("DbConnection.executescript ERROR: not connected")
			raise RuntimeError('Not connected')

	def commit(self):
		_LOG.debug('DbConnection.commit')
		if self._connection:
			self._connection.commit()
		else:
			_LOG.error("DbConnection.commit ERROR: not connected")
			raise RuntimeError('Not connected')

	def rollback(self):
		_LOG.debug('DbConnection.rollback')
		if self._connection:
			self._connection.rollback()
		else:
			_LOG.error("DbConnection.rollback ERROR: not connected")
			raise RuntimeError('Not connected')


class Column(object):
	"""Column definition"""
	def __init__(self, name=None, value_type=None, default=None,
			primary_key=False):
		self.name = name
		self.value_type = value_type  # convert type, None=don't change
		self.default = default
		self.primary_key = primary_key

	def __repr__(self):
		return ' '.join(map(str, ('<Column', self.name, self.value_type,
			self.default, self.primary_key, '>')))

	def from_database(self, value):
		if self.value_type is None:
			return value
		return self.value_type(value)

	def to_database(self, value):
		return value


class ManyToOne(object):
	"""Many to one relation definition"""
	# TODO: obsluga kluczy wielowartościowych
	def __init__(self, ref_field, ref_class, ref_key="id"):
		self.ref_field = ref_field
		self.ref_class = ref_class
		self.ref_key = ref_key

	def __repr__(self):
		return ' '.join(map(str, ('<ManyToOne', self.ref_field, self.ref_class,
				self.ref_key, '>')))

	def load(self, parent):
		ref_field_value = getattr(parent, self.ref_field)
		return self.ref_class.get(**{self.ref_key: ref_field_value})

	def save(self, parent, obj):
		if not isinstance(obj, self.ref_class):
			raise TypeError("wrong object type")
		obj_id = getattr(obj, self.ref_key)
		setattr(parent, self.ref_field, obj_id)


class _MetaModel(type):
	"""MetaModel for Model class"""
	def __new__(mcs, name, bases, dict_):
		if '_fields' in dict_:
			if '_primary_keys' not in dict_:
				dict_['_primary_keys'] = []
			fields = dict_['_fields']
			if isinstance(fields, (list, tuple, set)):
				rfields = {}
				for field in fields:
					if isinstance(field, Column):
						if not field.name:
							raise TypeError('No field name')
						rfields[field.name] = field
					elif isinstance(field, (str, unicode)):
						rfields[field] = Column(name=field)
					else:
						raise TypeError('Invalid column definition %r'
								% field)
				dict_['_fields'] = rfields
			dict_['_primary_keys'] = set(dict_['_primary_keys'])
			relations = dict_.get('_relations')
			if relations:
				for key, relation in relations.iteritems():
					dict_[key] = property(relation.load, relation.save)
		return type.__new__(mcs, name, bases, dict_)

	def __init__(mcs, name, bases, dict_):
		type.__init__(mcs, name, bases, dict_)
		if '_fields' in dict_:
			fields = dict_['_fields']
			primary_keys = dict_['_primary_keys']
			if isinstance(fields, dict):
				for key, value in fields.iteritems():
					if isinstance(value, Column):
						if not value.name:
							value.name = key
						if value.primary_key:
							if value.name not in primary_keys:
								primary_keys.add(value.name)
					elif isinstance(value, (str, unicode)):
						fields[key] = Column(name=value,
								primary_key=(value in primary_keys))
					else:
						fields[key] = Column(name=key)


class Model(object):
	"""Base class for all objects"""
	__metaclass__ = _MetaModel

	# table name in database
	_table_name = None

	# map class property -> None | db field name (str) | Column()
	_fields = {}

	# list of primary keys properties
	_primary_keys = set()

	# map property -> relation definion; create property for access to related
	# objects (get, set)
	_relations = {}

	# default sort order
	_default_sort_order = None

	def __new__(cls, *args, **kwarg):
		instance = object.__new__(cls, *args, **kwarg)
		# prepare instance
		if hasattr(cls, '_fields'):
			for key, column_def in cls._fields.iteritems():
				instance.__dict__[key] = column_def.default
		return instance

	def __init__(self, _is_new=True, **kwargs):
		super(Model, self).__init__()
		self._is_new = _is_new
		if kwargs:
			self.load_from_dict(kwargs)

	def __repr__(self):
		res = ['<', self.__class__.__name__,
				'TABLE=%r' % self._table_name]
		res.extend('%r=%r' % (key, val) for key, val
				in self.__dict__.iteritems()
				if key[0] != '_')
		res.append('>')
		return ' '.join(res)

	def load_from_dict(self, dict_):
		for key, val in dict_.iteritems():
			if key in self._fields:
				setattr(self, key, val)

	@property
	def connection(cls):
		return DbConnection()

	@classmethod
	def select(cls, order=None, limit=None, offset=None, distinct=None,
				where_stmt=None, group_by=None, count=False, **where):
		"""Select object according to given params """
		sql, query_params = cls._create_select_query(order, limit, offset,
				distinct, where_stmt, group_by, count, **where)
		with DbConnection().get_cursor() as cursor:
			cursor.execute(sql, query_params)
			for row in cursor:
				values = dict((key, cls._fields[key].from_database(val))
						for key, val in dict(row).iteritems())
				yield cls(_is_new=False, **values)

	@classmethod
	@cached(ttl=1)
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

	@classmethod
	def exists(cls, **pkeys):
		sql, query_params = cls._create_select_query(count=True, **pkeys)
		with DbConnection().get_cursor() as cursor:
			cursor.execute(sql, query_params)
			return cursor.fetchone()[0] > 0

	def save_or_update(self, commit=False):
		if self._is_new:
			self.save()
		else:
			self.update()
		if commit:
			self.connection.commit()

	def save(self):
		"""Save (insert) current object as new record."""
		sql, query_params = self._create_save_stmt()
		_LOG.debug("%s._save_new_object sql=%r params=%r",
				self.__class__.__name__, sql,
				query_params)
		with DbConnection().get_cursor() as cursor:
			cursor.execute(sql, query_params)
			rowid = cursor.lastrowid
			# update from db
			sql, query_params = self.__class__._create_select_query(limit=1,
					rowid=rowid)
			cursor.execute(sql, query_params)
			row = cursor.fetchone()
			for key, val in dict(row).iteritems():
				if key in self._fields:
					setattr(self, key, self._fields[key].from_database(val))
			self._is_new = False
		self.get.cache.clear()

	def update(self):
		"""Update current object.
			NOTE: this use primary key for select updated obj.
		"""
		sql, query_params = self._create_update_stmt()
		_LOG.debug("%s._update_object sql=%r params=%r",
				self.__class__.__name__, sql, query_params)
		with DbConnection().get_cursor() as cursor:
			cursor.execute(sql, query_params)
		self.get.cache.clear()

	def delete(self):
		"""Delete current object.
			NOTE: valid primary key is required.
		"""
		sql, query_params = self._create_delete_stmt()
		_LOG.debug("%s._update_object sql=%r params=%r",
				self.__class__.__name__, sql, query_params)
		with DbConnection().get_cursor() as cursor:
			cursor.execute(sql, query_params)
		self.get.cache.clear()

	@classmethod
	def _create_select_query(cls, order=None, limit=None, offset=None,
				distinct=None, where_stmt=None, group_by=None, count=False,
				**where):
		"""Prepare select query for given parameters """
		sqls = ['SELECT', ("DISTINCT" if distinct else "")]
		if count:
			sqls.append('COUNT(*) as count')
		else:
			# use "AS" if object fields is different from table column
			sqls.append(', '.join(((field.name + " AS " + key)
					if (field.name and field.name != key) else key)
					for key, field in cls._fields.iteritems()))
		sqls.append('FROM "%s"' % cls._table_name)
		query_params = []
		if where_stmt or where:
			sqls.append('WHERE')
			where_params = []
			if where_stmt:
				where_params.append(where_stmt)
			if where:
				for column, value in where.iteritems():
					column_name = (cls._fields[column].name or column
							if column in cls._fields else column)
					where_params.append("%s=?" % column_name)
					query_params.append(value)
			sqls.append(' AND '.join(where_params))
		if group_by:
			sqls.append("GROUP BY %s" % group_by)
		if order or cls._default_sort_order:
			sqls.append('ORDER BY %s' % (order or cls._default_sort_order))
		if limit:
			sqls.append('LIMIT %d' % limit)
		if offset:
			sqls.append('OFFSET %d' % offset)
		sql = ' '.join(sqls)
		_LOG.debug("Query.select sql=%r", sql)
		return sql, query_params

	def _create_update_stmt(self):
		"""Prepare sql stmt and parameters for update current object."""
		pkeys = self._get_pkey_values()
		if not pkeys or not all(pkey[1] for pkey in pkeys):
			raise RuntimeError('Missing primary keys')
		values = self._get_attr_values(False)
		sql = ['UPDATE', self._table_name, 'SET']
		sql.append(', '.join(val[0] + "=?" for val in values))
		sql.append('WHERE')
		sql.append(' AND '.join(val[0] + "=?" for val in pkeys))
		sql = ' '.join(sql)
		query_params = [val[1] for val in itertools.chain(values, pkeys)]
		return sql, query_params

	def _create_save_stmt(self):
		"""Prepare sql for save (insert) new object"""
		values = self._get_attr_values(True)
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
		pkeys = self._get_pkey_values()
		if not pkeys or not all(pkey[1] for pkey in pkeys):
			raise RuntimeError('Missing primary keys')
		sql = ['DELETE FROM', self._table_name, 'WHERE']
		sql.append(' AND '.join(val[0] + "=?" for val in pkeys))
		sql = ' '.join(sql)
		query_params = [val[1] for val in pkeys]
		return sql, query_params

	def _get_pkey_values(self):
		'''Get [(primary key, value)] '''
		fields = self._fields
		return [(fields[key].name or key,
				fields[key].to_database(getattr(self, key)))
				for key in self._primary_keys]

	def _get_attr_values(self, with_pkeys=False):
		'''Get [(column, value)] for all columns with primary key or without'''
		if with_pkeys:
			return [(field.name or key, field.to_database(getattr(self, key)))
					for key, field in self._fields.iteritems()]
		else:
			return [((field.name or key), field.to_database(getattr(self, key)))
					for key, field in self._fields.iteritems()
					if key not in self._primary_keys]
