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
    name = os.path.split(os.path.dirname(sys.argv[0]))[-1]
    parser    = argparse.ArgumentParser(prog=name, description='AZOTEA GUI')

    # Global options
    parser.add_argument('--version', action='version', version='{0} {1}'.format(name, __version__))
    parser.add_argument('-d', '--dbase',    type=str, required=True, action='store', metavar='<file path>', help='SQLite database to operate upon')
    parser.add_argument('-c', '--console', action='store_true',  help='log to console.')
    parser.add_argument('-l', '--log-file', type=str, default=None, action='store', metavar='<file path>', help='log to file')
   
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
    parser_batch.add_argument('--depth',      type=int, default=None, help='Specify images dir max. scanning depth')
    group = parser_batch.add_mutually_exclusive_group()
    group.add_argument('--only-sky',  action='store_true', help='only compute sky background')
    group.add_argument('--only-load', action='store_true', help='only loads images to database')
    group.add_argument('--only-publish', action='store_true', help='only publish to server')
    # only makes sense after image background computation
    parser_batch.add_argument('--publish',   action='store_true',  help='optionally publish to server')
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
    from azotea.gui.service import GraphicalService
    guiService = GraphicalService()
    guiService.setName(GraphicalService.NAME)
    guiService.setServiceParent(application)
elif options.command == 'batch':
    batchService = BatchService(
        images_dir = options.images_dir, 
        depth      = options.depth, 
        only_load  = options.only_load, 
        only_sky   = options.only_sky,
        only_pub   = options.only_publish,
        also_pub   = options.publish
        )
    batchService.setName(BatchService.NAME)
    batchService.setServiceParent(application)

# Start the ball rolling
service.IService(application).startService()
reactor.run()
sys.exit(get_status_code())