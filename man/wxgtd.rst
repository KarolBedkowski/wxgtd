==========
 wxGTD
==========

-----------------------------------
wxgtd
-----------------------------------

:Author: Karol Będkowski
:Date:   2013-05-07
:Copyright: Copyright(c) Karol Będkowski, 2013
:Version: 0.2.x
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

-d, --debug  Enable debug messages
-h, --help   Show help message and exit
--version    Show information about application version

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
