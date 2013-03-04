# -*- coding: utf-8 -*-

"""
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2009-2013"
__version__ = "2011-05-15"

from unittest import main, TestCase

from sorm import DbConnection, Model


class _Obj1(Model):
	_table_name = 'obj'
	_fields = {'id': None,
			'tekst': 'tekst1',
			'info': 'tekst2',
			'num': None}
	_primary_keys = ['id']

	def __init__(self, **kwarg):
		Model.__init__(self, **kwarg)


_OBJ1_DDL = """create table obj
(id integer primary key autoincrement,
tekst1 varchar,
tekst2 varchar,
num number);
"""


def _prepare_db():
	dbcon = DbConnection()
	dbcon.open(':memory:')
	dbcon.execue(_OBJ1_DDL)
	return dbcon


class TestEnum(TestCase):
	def test_01_create(self):
		obj = _Obj1()
		self.assert_(hasattr(obj, 'id'))
		self.assert_(hasattr(obj, 'tekst'))
		self.assert_(hasattr(obj, 'info'))
		self.assert_(hasattr(obj, 'num'))

	def test_02_create(self):
		obj = _Obj1(id=1, tekst='abc')
		obj.info = 'info123'
		obj.num = 'num123'
		self.assertEqual(obj.id, 1)
		self.assertEqual(obj.tekst, 'abc')
		self.assertEqual(obj.info, 'info123')
		self.assertEqual(obj.num, 'num123')

	def test_03_insert(self):
		dbcon = _prepare_db()
		obj = _Obj1(id=1, tekst='abc')
		obj.save()
		# raw check
		curs = dbcon.get_raw_cursor()
		curs.execute('select count(*) from obj where id=1')
		self.assertEqual(curs.fetchone()[0], 1)
		curs.close()
		dbcon.close()

	def test_04_query(self):
		dbcon = _prepare_db()
		obj = _Obj1(id=1, tekst='abc', info='info123', num=987)
		obj.save()
		obj2 = _Obj1.get(id=1)
		self.assertIsNotNone(obj2, "Object loaded")
		self.assertEqual(obj2.id, obj.id)
		self.assertEqual(obj2.tekst, obj.tekst)
		self.assertEqual(obj2.info, obj.info)
		self.assertEqual(obj2.num, obj.num)
		dbcon.close()

	def test_05_update(self):
		dbcon = _prepare_db()
		obj = _Obj1(id=1, tekst='abc', info='info123', num=987)
		obj.save()
		obj2 = _Obj1.get(id=1)
		self.assertIsNotNone(obj2, "Object loaded")
		self.assertEqual(obj2.id, obj.id)
		self.assertEqual(obj2.tekst, obj.tekst)
		self.assertEqual(obj2.info, obj.info)
		self.assertEqual(obj2.num, obj.num)
		obj2.tekst = 'cad'
		obj2.info = 'info321'
		obj2.update()
		obj3 = _Obj1.get(id=1)
		self.assertIsNotNone(obj3, "Object loaded")
		self.assertEqual(obj3.id, obj.id)
		self.assertEqual(obj3.tekst, 'cad')
		self.assertEqual(obj3.info, 'info321')
		self.assertEqual(obj3.num, 987)
		dbcon.close()

	def test_06_delete(self):
		dbcon = _prepare_db()
		obj = _Obj1(id=1, tekst='abc', info='info123', num=987)
		obj.save()
		obj2 = _Obj1.get(id=1)
		obj2.delete()
		obj3 = _Obj1.get(id=1)
		self.assertIsNone(obj3, "Object deleted")
		dbcon.close()


if __name__ == '__main__':
	main()
