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
\
TYPES = {TYPE_TASK: _("Task"),
		TYPE_PROJECT: _("Project"),
		TYPE_CHECKLIST: _("Checklist"),
		TYPE_CHECKLIST_ITEM: _("Checklist Item"),
		4: _("Note"),
		5: _("Call"),
		6: _("Email"),
		7: _("SMS"),
		8: _("Return Call")}


# Hide until patterns
HIDE_PATTERNS = {
		1: _("Task Is Due"),
		2: _("Given Date"),
		3: _("Week Before Due"),
		4: _("Day Before Start Date"),
		6: _("Week Before Start Date"),
		7: _("One Month Before Due"),
		8: _("Two Months Before Due"),
		9: _("Three Months Before Due"),
		10: _("Four Months Before Due"),
		11: _("Five Months Before Due"),
		12: _("Six Months Before Due"),
		13: _("One Month Before Start"),
		14: _("Two Months Before Start"),
		15: _("Three Months Before Start"),
		16: _("Four Months Before Start"),
		17: _("Five Months Before Start"),
		18: _("Six Months Before Start")}

HIDE_PATTERNS_MAP_EXP = {
		1: "task is due",
		2: "given date",
		3: "1 week before due",
		5: "1 day before start",
		6: "1 week before start",
		7: "1 month before due",
		8: "2 months before due",
		9: "3 months before due",
		10: "4 months before due",
		11: "5 months before due",
		12: "6 months before due",
		13: "1 month before start",
		14: "2 months before start",
		15: "3 months before start",
		16: "4 months before start",
		17: "5 months before start",
		18: "6 months before start"}

HIDE_PATTERNS_MAP_IMP = {
		"task is due": 1,
		"given date": 2,
		"1 week before due": 3,
		"1 day before start": 5,
		"1 week before start": 6,
		"1 month before due": 7,
		"2 months before due": 8,
		"3 months before due": 9,
		"4 months before due": 10,
		"5 months before due": 11,
		"6 months before due": 12,
		"1 month before start": 13,
		"2 months before start": 14,
		"3 months before start": 15,
		"4 months before start": 16,
		"5 months before start": 17,
		"6 months before start": 18}

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
		("16 days", _("16 days")),
		("30 days", _("30 days"))]

REMAIND_PATTERNS = dict(REMAIND_PATTERNS_LIST)
