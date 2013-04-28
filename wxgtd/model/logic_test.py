# -*- coding: utf-8 -*-

""" Tests for logic module.
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2013"
__version__ = "2013-04-17"

import copy
from unittest import main, TestCase
from datetime import datetime

from wxgtd.model import logic


class _FTask(object):
	def __init__(self, due_date=None, start_date=None, alarm_pattern=None):
		self.alarm_pattern = alarm_pattern
		self.start_date = start_date
		self.due_date = due_date
		self.alarm = None
		self.hide_until = None
		self.hide_pattern = None
		self.repeat_pattern = None
		self.repeat_from = 0
		self.parent_uuid = 1
		self.parent = None
		self.completed = None

	def clone(self):
		return copy.copy(self)

	def __eq__(self, obj):
		if type(obj) != type(self):
			return False
		for attr, val in self.__dict__.iteritems():
			if attr[0] == '_' or isinstance(val, _FTask):
				continue
			if getattr(obj, attr) != val:
				print attr, repr(getattr(obj, attr)), repr(val)
				return False
		return True


class TestLogicUpdateTaskAlarm(TestCase):
	def test_01_empty(self):
		obj = _FTask(None, None, None)
		logic.update_task_alarm(obj)
		self.assertIsNone(obj.alarm)

	def test_02_due(self):
		obj = _FTask(datetime.now(), None, 'due')
		logic.update_task_alarm(obj)
		self.assertEqual(obj.alarm, obj.due_date)

	def test_03_minutes(self):
		now = datetime(2000, 1, 2, 3, 4, 5)
		obj = _FTask(now, None, '1 minute')
		logic.update_task_alarm(obj)
		self.assertEqual(obj.alarm,  datetime(2000, 1, 2, 3, 3, 5))
		obj = _FTask(now, None, '30 minutes')
		logic.update_task_alarm(obj)
		self.assertEqual(obj.alarm,  datetime(2000, 1, 2, 2, 34, 5))
		obj = _FTask(now, None, '90 minutes')
		logic.update_task_alarm(obj)
		self.assertEqual(obj.alarm,  datetime(2000, 1, 2, 1, 34, 5))

	def test_04_hours(self):
		now = datetime(2000, 1, 2, 3, 4, 5)
		obj = _FTask(now, None, '1 hour')
		logic.update_task_alarm(obj)
		self.assertEqual(obj.alarm,  datetime(2000, 1, 2, 2, 4, 5))
		obj = _FTask(now, None, '25 hours')
		logic.update_task_alarm(obj)
		self.assertEqual(obj.alarm,  datetime(2000, 1, 1, 2, 4, 5))
		obj = _FTask(now, None, '1.5 hours')
		logic.update_task_alarm(obj)
		self.assertEqual(obj.alarm,  datetime(2000, 1, 2, 1, 34, 5))

	def test_05_days(self):
		now = datetime(2000, 1, 2, 3, 4, 5)
		obj = _FTask(now, None, '1 day')
		logic.update_task_alarm(obj)
		self.assertEqual(obj.alarm,  datetime(2000, 1, 1, 3, 4, 5))
		obj = _FTask(now, None, '30 days')
		logic.update_task_alarm(obj)
		self.assertEqual(obj.alarm,  datetime(1999, 12, 3, 3, 4, 5))


class TestLogicUpdateTaskHide(TestCase):
	def test_01_empty(self):
		obj = _FTask(None, None, None)
		obj.hide_pattern = None
		logic.update_task_hide(obj)
		self.assertIsNone(obj.hide_until)

	def test_02_given_date(self):
		obj = _FTask(None, None, None)
		self.hide_until = datetime.now()
		obj.hide_pattern = None
		logic.update_task_hide(obj)
		self.assertEqual(obj.hide_until, None)

	def test_03_task_is_due(self):
		now = datetime(2012, 1, 2, 3, 4, 5)
		obj = _FTask(now, None, None)
		obj.hide_pattern = "task is due"
		logic.update_task_hide(obj)
		self.assertEqual(obj.hide_until, now)

	def test_04_week(self):
		due = datetime(2012, 6, 15, 3, 4, 5)
		start = datetime(2010, 6, 15, 3, 4, 5)
		obj = _FTask(due, start, None)
		obj.hide_pattern = "1 week before due"
		logic.update_task_hide(obj)
		self.assertEqual(obj.hide_until, datetime(2012, 6, 8, 3, 4, 5))
		obj.hide_pattern = "2 weeks before start"
		logic.update_task_hide(obj)
		self.assertEqual(obj.hide_until, datetime(2010, 6, 1, 3, 4, 5))

	def test_05_day(self):
		due = datetime(2012, 6, 15, 3, 4, 5)
		start = datetime(2010, 6, 15, 3, 4, 5)
		obj = _FTask(due, start, None)
		obj.hide_pattern = "1 day before due"
		logic.update_task_hide(obj)
		self.assertEqual(obj.hide_until, datetime(2012, 6, 14, 3, 4, 5))
		obj.hide_pattern = "2 days before start"
		logic.update_task_hide(obj)
		self.assertEqual(obj.hide_until, datetime(2010, 6, 13, 3, 4, 5))

	def test_05_month(self):
		due = datetime(2012, 6, 15, 3, 4, 5)
		start = datetime(2010, 6, 15, 3, 4, 5)
		obj = _FTask(due, start, None)
		obj.hide_pattern = "1 month before due"
		logic.update_task_hide(obj)
		self.assertEqual(obj.hide_until, datetime(2012, 5, 15, 3, 4, 5))
		obj.hide_pattern = "2 months before start"
		logic.update_task_hide(obj)
		self.assertEqual(obj.hide_until, datetime(2010, 4, 15, 3, 4, 5))


class TestRepeatTask(TestCase):
	def test_01_empty(self):
		obj = _FTask(None, None, None)
		obj.repeat_pattern = None
		obj2 = logic.repeat_task(obj)
		self.assertIsNone(obj2)

	def test_02_daily(self):
		obj = _FTask(None, None, None)
		obj.repeat_pattern = 'Daily'
		obj2 = logic.repeat_task(obj, False)
		self.assertEqual(obj, obj2)
		self.assertIsNone(obj2.completed)

	def test_03_daily_compl_due(self):
		start = datetime(2000, 6, 15, 3, 4, 5)
		due = datetime(2005, 6, 15, 3, 4, 5)
		obj = _FTask(due, start, None)
		obj.repeat_pattern = 'Daily'
		obj.repeat_from = 1  # completed
		obj.completed = datetime(2010, 6, 15, 3, 4, 5)
		obj2 = logic.repeat_task(obj)
		self.assertEqual(obj2.due_date, datetime(2010, 6, 16, 3, 4, 5))
		# n.start =  start +  ( 20100616 (n.due) - 20050615 (due))
		# n.start =  start + 1827d
		self.assertEqual(obj2.start_date, datetime(2005, 6, 16, 3, 4, 5))

	def test_04_daily_due_due(self):
		start = datetime(2000, 6, 15, 3, 4, 5)
		due = datetime(2005, 6, 15, 3, 4, 5)
		obj = _FTask(due, start, None)
		obj.repeat_pattern = 'Daily'
		obj.repeat_from = 0  # due
		obj.completed = datetime(2010, 6, 15, 3, 4, 5)
		obj2 = logic.repeat_task(obj)
		self.assertEqual(obj2.due_date, datetime(2005, 6, 16, 3, 4, 5))
		self.assertEqual(obj2.start_date, datetime(2000, 6, 16, 3, 4, 5))

	def test_05_daily_compl_start(self):
		start = datetime(2000, 6, 15, 3, 4, 5)
		due = None  # no due
		obj = _FTask(due, start, None)
		obj.repeat_pattern = 'Daily'
		obj.repeat_from = 1  # completed
		obj.completed = datetime(2010, 6, 15, 3, 4, 5)
		obj2 = logic.repeat_task(obj)
		self.assertEqual(obj2.start_date, datetime(2010, 6, 16, 3, 4, 5))

	def test_06_daily_due_start(self):
		start = datetime(2000, 6, 15, 3, 4, 5)
		due = None  # no due
		obj = _FTask(due, start, None)
		obj.repeat_pattern = 'Daily'
		obj.repeat_from = 0  # due
		obj.completed = datetime(2010, 6, 15, 3, 4, 5)
		obj2 = logic.repeat_task(obj)
		self.assertEqual(obj2.start_date, datetime(2000, 6, 16, 3, 4, 5))

	def test_07_businessday_compl_start(self):
		start = datetime(2000, 6, 15, 3, 4, 5)
		due = None  # no due
		obj = _FTask(due, start, None)
		obj.repeat_pattern = 'Businessday'
		obj.repeat_from = 1  # completed
		obj.completed = datetime(2010, 6, 15, 3, 4, 5)  # wt
		obj2 = logic.repeat_task(obj, False)
		self.assertEqual(obj2.start_date, datetime(2010, 6, 16, 3, 4, 5))
		obj.completed = datetime(2010, 6, 16, 3, 4, 5)  # sr
		obj2 = logic.repeat_task(obj, False)
		self.assertEqual(obj2.start_date, datetime(2010, 6, 17, 3, 4, 5))
		obj.completed = datetime(2010, 6, 17, 3, 4, 5)  # cz
		obj2 = logic.repeat_task(obj, False)
		self.assertEqual(obj2.start_date, datetime(2010, 6, 18, 3, 4, 5))
		obj.completed = datetime(2010, 6, 18, 3, 4, 5)  # pt
		obj2 = logic.repeat_task(obj, False)
		self.assertEqual(obj2.start_date, datetime(2010, 6, 21, 3, 4, 5))
		obj.completed = datetime(2010, 6, 19, 3, 4, 5)  # so
		obj2 = logic.repeat_task(obj, False)
		self.assertEqual(obj2.start_date, datetime(2010, 6, 21, 3, 4, 5))
		obj.completed = datetime(2010, 6, 20, 3, 4, 5)  # n
		obj2 = logic.repeat_task(obj, False)
		self.assertEqual(obj2.start_date, datetime(2010, 6, 21, 3, 4, 5))
		obj.completed = datetime(2010, 6, 21, 3, 4, 5)  # pn
		obj2 = logic.repeat_task(obj, False)
		self.assertEqual(obj2.start_date, datetime(2010, 6, 22, 3, 4, 5))

	def test_08_weekend_compl_start(self):
		start = datetime(2000, 6, 15, 3, 4, 5)
		due = None  # no due
		obj = _FTask(due, start, None)
		obj.repeat_pattern = 'Weekend'
		obj.repeat_from = 1  # completed
		obj.completed = datetime(2010, 6, 15, 3, 4, 5)  # wt
		obj2 = logic.repeat_task(obj, False)
		self.assertEqual(obj2.start_date, datetime(2010, 6, 19, 3, 4, 5))
		obj.completed = datetime(2010, 6, 16, 3, 4, 5)  # sr
		obj2 = logic.repeat_task(obj, False)
		self.assertEqual(obj2.start_date, datetime(2010, 6, 19, 3, 4, 5))
		obj.completed = datetime(2010, 6, 17, 3, 4, 5)  # cz
		obj2 = logic.repeat_task(obj, False)
		self.assertEqual(obj2.start_date, datetime(2010, 6, 19, 3, 4, 5))
		obj.completed = datetime(2010, 6, 18, 3, 4, 5)  # pt
		obj2 = logic.repeat_task(obj, False)
		self.assertEqual(obj2.start_date, datetime(2010, 6, 19, 3, 4, 5))
		obj.completed = datetime(2010, 6, 19, 3, 4, 5)  # so
		obj2 = logic.repeat_task(obj, False)
		self.assertEqual(obj2.start_date, datetime(2010, 6, 20, 3, 4, 5))
		obj.completed = datetime(2010, 6, 20, 3, 4, 5)  # n
		obj2 = logic.repeat_task(obj, False)
		self.assertEqual(obj2.start_date, datetime(2010, 6, 26, 3, 4, 5))
		obj.completed = datetime(2010, 6, 21, 3, 4, 5)  # pn
		obj2 = logic.repeat_task(obj, False)
		self.assertEqual(obj2.start_date, datetime(2010, 6, 26, 3, 4, 5))

	def test_09_weekly_compl_start(self):
		obj = _FTask(None, datetime(2000, 6, 15, 3, 4, 5), None)
		obj.repeat_pattern = 'Weekly'
		obj.repeat_from = 1  # completed
		obj.completed = datetime(2010, 6, 15, 3, 4, 5)
		obj2 = logic.repeat_task(obj, False)
		self.assertEqual(obj2.start_date, datetime(2010, 6, 22, 3, 4, 5))
		obj.completed = datetime(2010, 6, 30, 3, 4, 5)
		obj2 = logic.repeat_task(obj, False)
		self.assertEqual(obj2.start_date, datetime(2010, 7, 7, 3, 4, 5))

	def test_10_biweekly_compl_start(self):
		obj = _FTask(None, datetime(2000, 6, 15, 3, 4, 5), None)
		obj.repeat_pattern = 'Biweekly'
		obj.repeat_from = 1  # completed
		obj.completed = datetime(2010, 6, 15, 3, 4, 5)
		obj2 = logic.repeat_task(obj, False)
		self.assertEqual(obj2.start_date, datetime(2010, 6, 29, 3, 4, 5))
		obj.completed = datetime(2010, 6, 30, 3, 4, 5)
		obj2 = logic.repeat_task(obj, False)
		self.assertEqual(obj2.start_date, datetime(2010, 7, 14, 3, 4, 5))

	def test_10_monthly_compl_start(self):
		obj = _FTask(None, datetime(2000, 6, 15, 3, 4, 5), None)
		obj.repeat_pattern = 'Monthly'
		obj.repeat_from = 1  # completed
		obj.completed = datetime(2010, 6, 15, 3, 4, 5)
		obj2 = logic.repeat_task(obj, False)
		self.assertEqual(obj2.start_date, datetime(2010, 7, 15, 3, 4, 5))
		obj.completed = datetime(2010, 6, 30, 3, 4, 5)
		obj2 = logic.repeat_task(obj, False)
		self.assertEqual(obj2.start_date, datetime(2010, 7, 30, 3, 4, 5))

	def test_11_bimonthly_compl_start(self):
		obj = _FTask(None, datetime(2000, 6, 15, 3, 4, 5), None)
		obj.repeat_pattern = 'Bimonthly'
		obj.repeat_from = 1  # completed
		obj.completed = datetime(2010, 6, 15, 3, 4, 5)
		obj2 = logic.repeat_task(obj, False)
		self.assertEqual(obj2.start_date, datetime(2010, 8, 15, 3, 4, 5))
		obj.completed = datetime(2010, 6, 30, 3, 4, 5)
		obj2 = logic.repeat_task(obj, False)
		self.assertEqual(obj2.start_date, datetime(2010, 8, 30, 3, 4, 5))

	def test_12_quarterly_compl_start(self):
		obj = _FTask(None, datetime(2000, 6, 15, 3, 4, 5), None)
		obj.repeat_pattern = 'Quarterly'
		obj.repeat_from = 1  # completed
		obj.completed = datetime(2010, 6, 15, 3, 4, 5)
		obj2 = logic.repeat_task(obj, False)
		self.assertEqual(obj2.start_date, datetime(2010, 9, 15, 3, 4, 5))
		obj.completed = datetime(2010, 6, 30, 3, 4, 5)
		obj2 = logic.repeat_task(obj, False)
		self.assertEqual(obj2.start_date, datetime(2010, 9, 30, 3, 4, 5))

	def test_13_semiannually_compl_start(self):
		obj = _FTask(None, datetime(2000, 6, 15, 3, 4, 5), None)
		obj.repeat_pattern = 'Semiannually'
		obj.repeat_from = 1  # completed
		obj.completed = datetime(2010, 6, 15, 3, 4, 5)
		obj2 = logic.repeat_task(obj, False)
		self.assertEqual(obj2.start_date, datetime(2010, 12, 15, 3, 4, 5))
		obj.completed = datetime(2010, 7, 30, 3, 4, 5)
		obj2 = logic.repeat_task(obj, False)
		self.assertEqual(obj2.start_date, datetime(2011, 1, 30, 3, 4, 5))

	def test_14_yearly_compl_start(self):
		obj = _FTask(None, datetime(2000, 6, 15, 3, 4, 5), None)
		obj.repeat_pattern = 'Yearly'
		obj.repeat_from = 1  # completed
		obj.completed = datetime(2010, 6, 15, 3, 4, 5)
		obj2 = logic.repeat_task(obj, False)
		self.assertEqual(obj2.start_date, datetime(2011, 6, 15, 3, 4, 5))
		obj.completed = datetime(2010, 7, 30, 3, 4, 5)
		obj2 = logic.repeat_task(obj, False)
		self.assertEqual(obj2.start_date, datetime(2011, 7, 30, 3, 4, 5))

	def test_15_xt(self):
		obj = _FTask(None, datetime(2000, 6, 15, 3, 4, 5), None)
		obj.repeat_from = 1  # completed
		obj.completed = datetime(2010, 6, 15, 3, 4, 5)
		obj.repeat_pattern = 'Every 6 days'
		obj2 = logic.repeat_task(obj, False)
		self.assertEqual(obj2.start_date, datetime(2010, 6, 21, 3, 4, 5))
		obj.repeat_pattern = 'Every 1 week'
		obj2 = logic.repeat_task(obj, False)
		self.assertEqual(obj2.start_date, datetime(2010, 6, 22, 3, 4, 5))
		obj.repeat_pattern = 'Every 2 months'
		obj2 = logic.repeat_task(obj, False)
		self.assertEqual(obj2.start_date, datetime(2010, 8, 15, 3, 4, 5))
		obj.repeat_pattern = 'Every 3 years'
		obj2 = logic.repeat_task(obj, False)
		self.assertEqual(obj2.start_date, datetime(2013, 6, 15, 3, 4, 5))

	def test_15_every_w_01(self):
		obj = _FTask(None, datetime(2000, 6, 15, 3, 4, 5), None)
		obj.repeat_from = 1  # completed
		obj.repeat_pattern = 'Every Mon'
		obj.completed = datetime(2010, 6, 15, 3, 4, 5)  # wt
		obj2 = logic.repeat_task(obj, False)
		self.assertEqual(obj2.start_date, datetime(2010, 6, 21, 3, 4, 5))
		obj.completed = datetime(2010, 6, 16, 3, 4, 5)  # sr
		obj2 = logic.repeat_task(obj, False)
		self.assertEqual(obj2.start_date, datetime(2010, 6, 21, 3, 4, 5))
		obj.completed = datetime(2010, 6, 21, 3, 4, 5)  # pn
		obj2 = logic.repeat_task(obj, False)
		self.assertEqual(obj2.start_date, datetime(2010, 6, 28, 3, 4, 5))

	def test_15_every_w_02(self):
		obj = _FTask(None, datetime(2000, 6, 15, 3, 4, 5), None)
		obj.repeat_from = 1  # completed
		obj.repeat_pattern = 'Every Mon, Thu'
		obj.completed = datetime(2010, 6, 15, 3, 4, 5)  # wt
		obj2 = logic.repeat_task(obj, False)
		self.assertEqual(obj2.start_date, datetime(2010, 6, 17, 3, 4, 5))
		obj.completed = datetime(2010, 6, 16, 3, 4, 5)  # sr
		obj2 = logic.repeat_task(obj, False)
		self.assertEqual(obj2.start_date, datetime(2010, 6, 17, 3, 4, 5))
		obj.completed = datetime(2010, 6, 17, 3, 4, 5)  # cz
		obj2 = logic.repeat_task(obj, False)
		self.assertEqual(obj2.start_date, datetime(2010, 6, 21, 3, 4, 5))
		obj.completed = datetime(2010, 6, 19, 3, 4, 5)  # so
		obj2 = logic.repeat_task(obj, False)
		self.assertEqual(obj2.start_date, datetime(2010, 6, 21, 3, 4, 5))

	def test_15_every_w_03(self):
		obj = _FTask(None, datetime(2000, 6, 15, 3, 4, 5), None)
		obj.repeat_from = 1  # completed
		obj.repeat_pattern = 'Every Mon, Thu, Wed, Fri, Sat, Sun, Tue'
		obj.completed = datetime(2010, 6, 15, 3, 4, 5)  # wt
		obj2 = logic.repeat_task(obj, False)
		self.assertEqual(obj2.start_date, datetime(2010, 6, 16, 3, 4, 5))
		obj.completed = datetime(2010, 6, 16, 3, 4, 5)  # sr
		obj2 = logic.repeat_task(obj, False)
		self.assertEqual(obj2.start_date, datetime(2010, 6, 17, 3, 4, 5))
		obj.completed = datetime(2010, 6, 17, 3, 4, 5)  # cz
		obj2 = logic.repeat_task(obj, False)
		self.assertEqual(obj2.start_date, datetime(2010, 6, 18, 3, 4, 5))
		obj.completed = datetime(2010, 6, 18, 3, 4, 5)  # pr
		obj2 = logic.repeat_task(obj, False)
		self.assertEqual(obj2.start_date, datetime(2010, 6, 19, 3, 4, 5))
		obj.completed = datetime(2010, 6, 19, 3, 4, 5)  # so
		obj2 = logic.repeat_task(obj, False)
		self.assertEqual(obj2.start_date, datetime(2010, 6, 20, 3, 4, 5))
		obj.completed = datetime(2010, 6, 20, 3, 4, 5)  # n
		obj2 = logic.repeat_task(obj, False)
		self.assertEqual(obj2.start_date, datetime(2010, 6, 21, 3, 4, 5))
		obj.completed = datetime(2010, 6, 21, 3, 4, 5)  # pn
		obj2 = logic.repeat_task(obj, False)
		self.assertEqual(obj2.start_date, datetime(2010, 6, 22, 3, 4, 5))

if __name__ == '__main__':
	main()
