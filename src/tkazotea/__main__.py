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

from tkazotea import __version__
from tkazotea.logger  import startLogging
from tkazotea.gui.service import GraphicalService
from tkazotea.batch.service import BatchService
from tkazotea.dbase.service import DatabaseService


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
    batchService = BatchService(options.work_dir)
    batchService.setName(BatchService.NAME)
    batchService.setServiceParent(application)

# Start the ball rolling
service.IService(application).startService()
reactor.run()