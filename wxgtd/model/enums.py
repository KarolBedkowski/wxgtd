#!/usr/bin/python
# -*- coding: utf-8 -*-

""" Constans and enums.

Copyright (c) Karol Będkowski, 2013

This file is part of wxGTD
Licence: GPLv2+
"""
__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2013"
__version__ = "2013-04-26"


import gettext

_ = gettext.gettext
ngettext = gettext.ngettext  # pylint: disable=C0103


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
#		TYPE_NOTE: _("Note"),
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


REMIND_PATTERNS_LIST = [
		('due', _("When task is due")),
		("1 minute", ngettext("%d minute", "%d minutes", 1) % 1),
		("5 minutes", ngettext("%d minute", "%d minutes", 5) % 5),
		("10 minutes", ngettext("%d minute", "%d minutes", 10) % 10),
		("15 minutes", ngettext("%d minute", "%d minutes", 15) % 15),
		("30 minutes", ngettext("%d minute", "%d minutes", 15) % 30),
		("45 minutes", ngettext("%d minute", "%d minutes", 15) % 45),
		("1 hour", ngettext("%d hour", "%d hours", 1) % 1),
		("1.5 hours", _("1.5 hours")),
		("2 hours", ngettext("%d hour", "%d hours", 2) % 2),
		("3 hours", ngettext("%d hour", "%d hours", 3) % 3),
		("4 hours", ngettext("%d hour", "%d hours", 4) % 4),
		("6 hours", ngettext("%d hour", "%d hours", 6) % 6),
		("8 hours", ngettext("%d hour", "%d hours", 8) % 8),
		("10 hours", ngettext("%d hour", "%d hours", 10) % 10),
		("12 hours", ngettext("%d hour", "%d hours", 12) % 12),
		("1 day",  ngettext("%d day", "%d days", 1) % 1),
		("2 days", ngettext("%d day", "%d days", 2) % 2),
		("3 days", ngettext("%d day", "%d days", 3) % 3),
		("4 days", ngettext("%d day", "%d days", 4) % 4),
		("5 days", ngettext("%d day", "%d days", 5) % 5),
		("6 days", ngettext("%d day", "%d days", 6) % 6),
		("7 days", ngettext("%d day", "%d days", 7) % 7),
		("14 days", ngettext("%d day", "%d days", 14) % 14),
		("30 days", ngettext("%d day", "%d days", 30) % 30)]

REMIND_PATTERNS = dict(REMIND_PATTERNS_LIST)

SNOOZE_PATTERNS = REMIND_PATTERNS_LIST[1:]

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
	('Last day of every month', _('Last day of every month')),
	("WITHPARENT", _("With parrent"))]

REPEAT_PATTERN = dict(REPEAT_PATTERN_LIST)

GOAL_TIME_TERM = {0: _("Lifelong"),
		1: _("Long Term"),
		2: _("Short Term")}
