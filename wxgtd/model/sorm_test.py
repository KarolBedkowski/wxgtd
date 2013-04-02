# -*- coding: utf-8 -*-

"""
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2009-2013"
__version__ = "2011-05-15"

from unittest import main, TestCase

from sorm import DbConnection, Model, Column, ManyToOne, OneToMany


class _Obj1(Model):
	_table_name = 'obj'
	_fields = {'id': None,
			'tekst': 'tekst1',
			'info': 'tekst2',
			'num': None}
	_primary_keys = ['id']

	def __init__(self, **kwarg):
		Model.__init__(self, **kwarg)


class _Obj2(Model):
	_table_name = 'obj'
	_primary_keys = ['id']
	_fields = {'id': Column(value_type=int),
			'name': None,
			'value': 'value'}

	def __init__(self, **kwarg):
		Model.__init__(self, **kwarg)
		self.id = None
		self.name = None
		self.value = None


_OBJ1_DDL = """create table obj
(id integer primary key autoincrement,
tekst1 varchar,
tekst2 varchar,
num number);

create table mobj
(id integer primary key autoincrement,
obj_id integer);
"""


class _Obj3(Model):
	_table_name = 'obj'
	_fields = {'id': Column(value_type=int, primary_key=True),
			'name': Column(name="col1", value_type=str),
			'value': Column(name="val", value_type=float)}


class _Obj4(Model):
	_table_name = 'obj'
	_fields = [Column(name="id", value_type=int, primary_key=True),
			Column(name="col1", value_type=str),
			Column(name="val", value_type=float)]


class _MObj(Model):
	_table_name = 'mobj'
	_fields = [Column(name="id", value_type=int, primary_key=True),
			Column(name="obj_id", value_type=int)]
	_relations = {'obj': ManyToOne('obj_id', _Obj1, "id")}


class _Obj6(Model):
	_table_name = 'obj'
	_fields = ['id', 'tekst1', 'tekst2', 'num']
	_primary_keys = ['id']
	_relations = {'objs': OneToMany("id", _MObj, "obj_id")}


def _prepare_db():
	dbcon = DbConnection()
	dbcon.open(':memory:')
	dbcon.execuescript(_OBJ1_DDL)
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
		# obj check
		self.assertTrue(_Obj1.exists(id=1))
		self.assertTrue(not _Obj1.exists(id=122))
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

	def test_07_full_select_query(self):
		sql, params = _Obj1._create_select_query(order="ord1 desc",
				limit=10, offset=20, distinct=True,
				where_stmt="(foo > 10 or foo < 5)",
				group_by="grouping sts",
				id=12, num=233)
		self.assertEqual(sql, 'SELECT DISTINCT tekst1 AS tekst, tekst2 AS info, '
				'num, id FROM "obj" WHERE (foo > 10 or foo < 5) AND num=? '
				'AND id=? GROUP BY grouping sts ORDER BY ord1 desc '
				'LIMIT 10 OFFSET 20')
		self.assertEqual(params, [233, 12])

	def test_07_auto_fields(self):
		obj = _Obj2()
		self.assertListEqual(sorted(obj._fields.keys()),
				sorted(['id', 'name', 'value']))

	def test_08_columns(self):
		obj = _Obj3()
		self.assertTrue(obj._fields['id'].primary_key)
		self.assertEqual(obj._fields['id'].name, 'id')
		self.assertEqual(obj._fields['name'].name, 'col1')
		self.assertEqual(obj._fields['value'].value_type, float)
		self.assertEqual(obj._primary_keys, set(['id']))

	def test_09_columns_list(self):
		obj = _Obj4()
		self.assertTrue(obj._fields['id'].primary_key)
		self.assertEqual(obj._fields['id'].name, 'id')
		self.assertEqual(obj._fields['col1'].name, 'col1')
		self.assertEqual(obj._fields['val'].value_type, float)
		self.assertEqual(obj._primary_keys, set(['id']))

	def test_10_autoincrement_pk(self):
		dbcon = _prepare_db()
		obj = _Obj1(tekst='abc', info='info123', num=987)
		obj.save()
		self.assertIsNotNone(obj.id, "PK not loaded")
		self.assertEqual(obj.id, 1, "PK not loaded")
		dbcon.close()

	def test_11_relations_def(self):
		self.assertTrue(hasattr(_MObj, 'obj'))

	def test_12_relation_get(self):
		dbcon = _prepare_db()
		obj = _Obj1(id=1, tekst='abc', info='info123', num=987)
		obj.save()
		mobj = _MObj(id=2, obj_id=1)
		mobj.save()
		mobj2 = _MObj.get(id=2)
		self.assertIsNotNone(mobj2, "Object loaded")
		self.assertEqual(mobj2.obj_id, mobj.obj_id)
		obj2 = mobj.obj
		self.assertIsNotNone(obj2)
		self.assertEqual(obj2.id, obj.id)
		self.assertEqual(obj2.tekst, obj.tekst)
		dbcon.close()

	def test_12_relation_set(self):
		dbcon = _prepare_db()
		obj = _Obj1(id=1, tekst='abc', info='info123', num=987)
		mobj = _MObj(id=2)
		mobj.obj = obj
		self.assertEqual(mobj.obj_id, obj.id)
		dbcon.close()

	def test_13_relation_one2many(self):
		"""testy dla relacji OneToMany"""
		dbcon = _prepare_db()
		obj = _Obj6(id=1, tekst1='abc', tekst2='info123', num=987)
		mobj1 = _MObj(id=2)
		mobj2 = _MObj(id=3)
		obj.objs = [mobj1, mobj2]
		self.assertListEqual(obj.objs, [mobj1, mobj2])
		obj.save()
		obj2 = _Obj6.get(id=1)
		objs = obj2.objs
		self.assertTrue(isinstance(objs, list), 'result must be list')
		self.assertEqual(len(objs), 2)
		mobj1_1 = _MObj.get(id=2)
		self.assertEqual(mobj1_1.obj_id, obj2.id, 'spr obj_id w relacji')
		dbcon.close()


if __name__ == '__main__':
	main()
