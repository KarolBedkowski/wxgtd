# -*- coding: utf-8 -*-

""" Database  objects definition.

Copyright (c) Karol Będkowski, 2013

This file is part of wxGTD
Licence: GPLv2+
"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2013"
__version__ = '2013-04-26'


SCHEMA_DEF = []

#SCHEMA_DEF.append(["""
#create table if not exists tasks (
	#parent_uuid varchar(36) references tasks(uuid),
	#uuid varchar(36) primary key,
	#created timestamp,
	#modified timestamp,
	#completed timestamp,
	#deleted timestamp,
	#ordinal integer,
	#title text,
	#note text,
	#type integer,
	#starred number,
	#status number,
	#priority number,
	#importance number,
	#start_date timestamp,
	#start_time_set number,
	#due_date timestamp,
	#due_date_project timestamp,
	#due_time_set number,
	#due_date_mod number,
	#floating_event number,
	#duration number,
	#energy_required number,
	#repeat_from number,
	#repeat_pattern text,
	#repeat_end number,
	#hide_pattern text,
	#hide_until timestamp,
	#prevent_auto_purge number,
	#trash_bin number,
	#metainf text,
	#folder_uuid varchar(36),
	#context_uuid varchar(36),
	#goal_uuid varchar(36))""",
	#"""
#create table if not exists folders (
	#parent_uuid integer references tasks(id),
	#uuid varchar(36) primary key,
	#created timestamp,
	#modified timestamp,
	#deleted timestamp,
	#ordinal integer,
	#title text,
	#note text,
	#color number,
	#visible number)""",
	#"""
#create table if not exists contexts (
	#parent_uuid varchar(36) references contexts(uuid),
	#uuid varchar(36) primary key,
	#created timestamp,
	#modified timestamp,
	#deleted timestamp,
	#ordinal integer,
	#title text,
	#note text,
	#color number,
	#visible number)""",
	#"""
#create table if not exists tasknotes (
	#task_uuid varchar(36) references tasks(uuid),
	#uuid varchar(36) primary key,
	#created timestamp,
	#modified timestamp,
	#ordinal integer,
	#title text,
	#color number,
	#visible number)""",
	#"""
#create table if not exists alarms (
	#task_uuid varchar(36) references tasks(uuid),
	#uuid varchar(36) primary key,
	#created timestamp,
	#modified timestamp,
	#alarm timestamp,
	#reminder number,
	#active number,
	#note text)""",
	#"""
#create table if not exists goals (
	#parent_uuid varchar(36) references goals(uuid),
	#uuid varchar(36) primary key,
	#created timestamp,
	#modified timestamp,
	#deleted timestamp,
	#ordinal integer,
	#title text,
	#note text,
	#time_period integer,
	#archived integer,
	#color number,
	#visible number)""",
	#"""
#create table if not exists tags (
	#parent_uuid varchar(36) references tags(uuid),
	#uuid varchar(36) primary key,
	#created timestamp,
	#modified timestamp,
	#deleted timestamp,
	#ordinal integer,
	#title text,
	#note text,
	#bg_color integer,
	#visible number)""",
	#"""
#create table if not exists task_tags (
	#task_uuid varchar(36) references tasks(uuid),
	#tag_uuid varchar(36) references tags(uuid),
	#created timestamp,
	#modified timestamp)""",
	#"""
#create table if not exists wxgtd (
	#key varchar(32) primary key,
	#val text)"""])


_SYNCLOG_SCHEME = """CREATE TABLE synclog (
device_id VARCHAR(50) NOT NULL,
sync_time DATETIME,
prev_sync_time DATETIME,
PRIMARY KEY (device_id, sync_time))"""


def fix_synclog(engine):
	""" Drop primary key from synclog.sync_time """
	res = engine.execute("select sql from sqlite_master where name='synclog'")
	rows = res.fetchall()
	if not rows or not rows[0]:
		return
	if 'PRIMARY KEY (device_id)' not in rows[0][0] and \
			'sync_time DATETIME NOT NULL' not in rows[0][0]:
		return
	engine.execute("alter table synclog rename to synclog_old")
	engine.execute(_SYNCLOG_SCHEME)
	with engine.begin() as conn:
		conn.execute("insert into synclog select device_id, sync_time, "
				"prev_sync_time from synclog")
	engine.execute("drop table synclog_old;")
