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

    group0 = parser.add_mutually_exclusive_group(required=True)
    group0.add_argument('--create', action='store_true', help='Create the database and exit')
    group0.add_argument('--gui', action='store_true',  help='Launch Azotea GUI')
    group0.add_argument('--batch',  action='store_true', help='launch Azotea in batch mode')

    parser.add_argument('--console', action='store_true',  help='log to console.')
    parser.add_argument('--log-file', type=str, default=None, action='store', metavar='<log file>', help='log to file')
    parser.add_argument('--dbase',    type=str, default="azotea.db", action='store', metavar='<SQLite database path>', help='SQLite database to operate upon')
   
    parser.add_argument('--images-dir', type=str, default=None, action='store', metavar='<path>', help='Images working directory')
    parser.add_argument('--csv-export-type', type=str, choices=["day", "month", "all"], default=None, help='(batch) What to export/publish in CSV')
    parser.add_argument('--csv-dir', type=str, default=None, help='(batch) CSV files base dir (optional)')
    parser.add_argument('--publish', action='store_true',  help='(batch) Also publish results to server')

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

dbaseService = DatabaseService(options.dbase, options.create)
dbaseService.setName(DatabaseService.NAME)
dbaseService.setServiceParent(application)

if options.gui:
	guiService = GraphicalService()
	guiService.setName(GraphicalService.NAME)
	guiService.setServiceParent(application)
elif options.batch:
    images_dir   = options.images_dir
    export_opt   = options.csv_export_type
    csv_dir      = options.csv_dir
    pub_flag     = options.publish
    batchService = BatchService(images_dir, export_opt, csv_dir, pub_flag)
    batchService.setName(BatchService.NAME)
    batchService.setServiceParent(application)

# Start the ball rolling
service.IService(application).startService()
reactor.run()