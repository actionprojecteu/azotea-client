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
from azotea.utils import get_status_code
from azotea.logger  import startLogging
from azotea.gui.service import GraphicalService
from azotea.batch.service import BatchService
from azotea.dbase.service import DatabaseService

import azotea.consent.form

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

    # --------------------------
    # Create first level parsers
    # --------------------------

    subparser = parser.add_subparsers(dest='command')

    parser_gui    = subparser.add_parser('gui', help='consent command')
    parser_batch  = subparser.add_parser('batch', help='observer commands')

    # -----------------------------
    # Arguments for 'batch' command
    # -----------------------------

    parser_batch.add_argument('--images-dir', type=str, default=None, action='store', metavar='<path>', help='Images working directory')

    return parser


def handle_agreement(options):
    if options.command == 'batch':
        connection = azotea.consent.form.get_database_connection(options.dbase)
        accepted = azotea.consent.form.check_agreement(connection)
        if not accepted:
            print("-"*22)
            print("Agreement not accepted")
            print("-"*22)
            sys.exit(126)
        connection.close()

# -------------------
# Booting application
# -------------------

options = createParser().parse_args(sys.argv[1:])
handle_agreement(options)

startLogging(
	console  = options.console,
	filepath = options.log_file
)

# -------------------
# Applcation assembly
# -------------------

application = service.Application("azotea")

dbaseService = DatabaseService(options.dbase, False)
dbaseService.setName(DatabaseService.NAME)
dbaseService.setServiceParent(application)

if options.command == 'gui':
	guiService = GraphicalService()
	guiService.setName(GraphicalService.NAME)
	guiService.setServiceParent(application)
elif options.command == 'batch':
    images_dir   = options.images_dir
    batchService = BatchService(images_dir)
    batchService.setName(BatchService.NAME)
    batchService.setServiceParent(application)

# Start the ball rolling
service.IService(application).startService()
reactor.run()
sys.exit(get_status_code())