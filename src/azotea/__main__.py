# ----------------------------------------------------------------------
# Copyright (c) 2020
#
# See the LICENSE file for details
# see the AUTHORS file for authors
# ----------------------------------------------------------------------


#--------------------
# System wide imports
# -------------------

import os
import sys
import argparse


# ---------------
# Twisted imports
# ---------------

from twisted.internet import reactor
from twisted.application import service

#--------------
# local imports
# -------------

from azotea import __version__
from azotea.logger  import startLogging
from azotea.gui.service import GraphicalService
from azotea.batch.service import BatchService
from azotea.dbase.service import DatabaseService


# ----------------
# Module constants
# ----------------

# -----------------------
# Module global variables
# -----------------------

# ------------------------
# Module utility functions
# ------------------------

def createParser():
    # create the top-level parser
    name = os.path.split(os.path.dirname(sys.argv[0]))[-1]
    parser    = argparse.ArgumentParser(prog=name, description='AZOTEA GUI')

    # Global options
    parser.add_argument('--version', action='version', version='{0} {1}'.format(name, __version__))
    parser.add_argument('--console', action='store_true',  help='log to console.')
    parser.add_argument('--log-file', type=str, default=None, action='store', metavar='<log file>', help='log to file')
    parser.add_argument('--dbase',    type=str, default="azotea.db", action='store', metavar='<SQLite database path>', help='SQLite database to operate upon')
    parser.add_argument('--no-gui',  action='store_true',  help='No GUI. Execute in batch mode.')
    parser.add_argument('--work-dir', type=str, default=None, action='store', metavar='<log file>', help='log to file')
    parser.add_argument('--csv-export-type', type=str, choices=["day", "month", "all"], default=None, help='What to export in CSV')
    parser.add_argument('--csv-file', type=str, default=None, help='Export CSV file path (optional)')

    return parser

# -------------------
# Applcation assembly
# -------------------

options = createParser().parse_args(sys.argv[1:])
startLogging(
	console  = options.console,
	filepath = options.log_file
)

application = service.Application("azotea")

dbaseService = DatabaseService(options.dbase)
dbaseService.setName(DatabaseService.NAME)
dbaseService.setServiceParent(application)

if not options.no_gui:
	guiService = GraphicalService()
	guiService.setName(GraphicalService.NAME)
	guiService.setServiceParent(application)
else:
    work_dir     = options.work_dir
    export_opt   = options.csv_export_type
    csv_path     = options.csv_file
    batchService = BatchService(work_dir, export_opt, csv_path)
    batchService.setName(BatchService.NAME)
    batchService.setServiceParent(application)

# Start the ball rolling
service.IService(application).startService()
reactor.run()