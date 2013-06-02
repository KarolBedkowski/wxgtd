==========
 wxGTD
==========

-----------------------------------
wxgtd_cli
-----------------------------------

:Author: Karol Będkowski
:Date:   2013-06-02
:Copyright: Copyright(c) Karol Będkowski, 2013
:Version: 0.x
:Manual section: 1
:Manual group: wxGTD Manual Pages


SYNOPSIS
========

wxgtd_cli

DESCRIPTION
===========

Desktop application for task management compatible with `DGT GTD`_.
CLI interface to database.

Support synchronisation data via sync file by Dropbox.

.. _`DGT GTD`: http://www.dgtale.ch/

OPTIONS
=======
--version             Show program's version number and exit
-h, --help            Show this help message and exit

List tasks
----------
  -t, --tasks         Show all tasks
  --hotlist           Show task in hotlist
  --starred           Show starred tasks
  --basket            Show tasks in basket
  --finished          Show finished tasks
  --projects          Show projects
  --checklists        Show checklists
  --future-alarms     Show task with alarms in future

Task operations
---------------
  -q QUICK_TASK_TITLE, --quick-task=QUICK_TASK_TITLE    
                      Quickly add new task

List tasks options
------------------
  --show-finished     Show finished tasks
  --show-subtask      Show subtasks
  --dont-hide-until   Show hidden task
  --parent=PARENT_UUID
                      Set parent UUID for query
  -s SEARCH_TEXT, --search=SEARCH_TEXT
                      Search for title/note
  -v, --verbose       Show more information
  --output-csv        Show result as csv file

Debug options
-------------
  -d, --debug         Enable debug messages
  --debug-sql         Enable sql debug messages


FILES
=======

~/.local/share/wxgtd/wxgtd.db
    Application database, contain all stored information.

~/.local/share/wxgtd/backups/
    Backups created before synchronization.

~/.config/wxgtd/wxgtd.cfg
    Application configuration file.

~/Dropbox/Apps/DGT-GTD/sync/GTD_SYNC.zip
    Default synchronization file.
