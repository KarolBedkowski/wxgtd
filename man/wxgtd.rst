==========
 wxGTD
==========

-----------------------------------
wxgtd
-----------------------------------

:Author: Karol Będkowski
:Date:   2013-06-02
:Copyright: Copyright(c) Karol Będkowski, 2013
:Version: 0.x
:Manual section: 1
:Manual group: wxGTD Manual Pages


SYNOPSIS
========

wxgtd

DESCRIPTION
===========

Desktop application for task management compatible with `DGT GTD`_.

Support synchronisation data via sync file by Dropbox.

.. _`DGT GTD`: http://www.dgtale.ch/


OPTIONS
=======

--version             Show program's version number and exit
-h, --help            Show this help message and exit

Creating tasks
--------------
  --quick-task-dialog
                      enable debug messages

Debug options
-------------
  -d, --debug         enable debug messages
  --debug-sql         enable sql debug messages
  --wx-inspection     run wx windows inspector

Other options
-------------
  --force-start       Force start application even other instance is running.


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
