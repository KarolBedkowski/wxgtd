#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Obiekty

"""
__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2013"
__version__ = "2013-03-02"


import gettext

_ = gettext.gettext


STATUSES = {0: _("No Status"),  # no status
		1: _("Next Action"),
		2: _("Active"),
		3: _("Planning"),
		4: _("Delegated"),
		5: _("Waiting"),
		6: _("Hold"),
		7: _("Postponed"),
		8: _("Someday"),
		9: _("Canceled"),
		10: _("Reference")}

TYPE_TASK = 0
TYPE_PROJECT = 1
TYPE_CHECKLIST = 2
TYPE_CHECKLIST_ITEM = 3
TYPE_NOTE = 4
TYPE_CALL = 5
TYPE_EMAIL = 6
TYPE_SMS = 7
TYPE_RETURN_CALL = 8

TYPES = {TYPE_TASK: _("Task"),
		TYPE_PROJECT: _("Project"),
		TYPE_CHECKLIST: _("Checklist"),
		TYPE_CHECKLIST_ITEM: _("Checklist Item"),
		TYPE_NOTE: _("Note"),
		TYPE_CALL: _("Call"),
		TYPE_EMAIL: _("Email"),
		TYPE_SMS: _("SMS"),
		TYPE_RETURN_CALL: _("Return Call")}


# Hide until patterns
HIDE_PATTERNS_LIST = [
		("task is due", _("Task Is Due")),
		("given date", _("Given Date")),
		("1 week before due", _("Week Before Due")),
		("1 day before due", _("Day Before Due")),
		("1 day before start", _("Day Before Start Date")),
		("1 week before start", _("Week Before Start Date")),
		("1 month before due", _("One Month Before Due")),
		("2 months before due", _("Two Months Before Due")),
		("3 months before due", _("Three Months Before Due")),
		("4 months before due", _("Four Months Before Due")),
		("5 months before due", _("Five Months Before Due")),
		("6 months before due", _("Six Months Before Due")),
		("1 month before start", _("One Month Before Start")),
		("2 months before start", _("Two Months Before Start")),
		("3 months before start", _("Three Months Before Start")),
		("4 months before start", _("Four Months Before Start")),
		("5 months before start", _("Five Months Before Start")),
		("6 months before start", _("Six Months Before Start"))]

HIDE_PATTERNS = dict(HIDE_PATTERNS_LIST)


REMAIND_PATTERNS_LIST = [
		('due', _("When task is due")),
		("1 minute", _("1 minute")),
		("5 minutes", _("5 minutes")),
		("10 minutes",  _("10 minutes")),
		("15 minutes", _("15 minutes")),
		("30 minutes", _("30 minutes")),
		("45 minutes", _("45 minutes")),
		("1 hour", _("1 hour")),
		("1.5 hours", _("1.5 hours")),
		("2 hours", _("2 hours")),
		("3 hours", _("3 hours")),
		("4 hours", _("4 hours")),
		("6 hours", _("6 hours")),
		("8 hours", _("8 hours")),
		("10 hours", _("10 hours")),
		("12 hours", _("12 hours")),
		("1 day", _("1 day")),
		("2 days", _("2 days")),
		("3 days", _("3 days")),
		("4 days", _("4 days")),
		("5 days", _("5 days")),
		("6 days", _("6 days")),
		("7 days", _("7 days")),
		("14 days", _("14 days")),
		("30 days", _("30 days"))]

REMAIND_PATTERNS = dict(REMAIND_PATTERNS_LIST)

PRIORITIES = {3: _("TOP"),
		2: _("High"),
		1: _("Med"),
		0: _("Low"),
		-1: _("None")}

REPEAT_PATTERN_LIST = [("Norepeat", _("Norepeat")),
	("Daily", _("Daily")),
	("BusinessDay", _("Business Day")),
	("Weekend", _("Weekend")),
	("Weekly", _("Weekly")),
	("Biweekly", _("Biweekly")),
	("Monthly", _("Monthly")),
	("Bimonthly", _("Bimonthly")),
	("Quarterly", _("Quarterly")),
	("Semiannually", _("Semiannually")),
	("Yearly", _("Yearly")),
	("WITHPARENT", _("With parrent"))]

REPEAT_PATTERN = dict(REPEAT_PATTERN_LIST)

GOAL_TIME_TERM = {0: _("Lifelong"),
		1: _("Long Term"),
		2: _("Short Term")}
