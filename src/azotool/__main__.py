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
from azotea.dbase.service import DatabaseService
from azotool.cli.service import CommandService

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

    parser_observer  = subparser.add_parser('observer', help='observer commands')
    parser_location  = subparser.add_parser('location', help='location commands')
    parser_camera   = subparser.add_parser('camera', help='camera commands')
    parser_roi    = subparser.add_parser('roi', help='roi commands')
    parser_misc = subparser.add_parser('miscelanea', help='miscelanea commands')
   
    # ------------------------------------------
    # Create second level parsers for 'observer'
    # ------------------------------------------

    subparser = parser_observer.add_subparsers(dest='subcommand')

    obscre = subparser.add_parser('create',  help="Create a new observer in the database")
    obscre.add_argument('--name',        type=str, nargs='+', required=True, help="Observer's name")
    obscre.add_argument('--surname',     type=str, nargs='+', required=True, help="Observer's surname")
    obscre.add_argument('--affiliation', type=str, nargs='+', required=True, help='Complete affiliation name')
    obscre.add_argument('--acronym',     type=str, nargs='+', required=True, help='Affiliation acronym')

    # ------------------------------------------
    # Create second level parsers for 'location'
    # ------------------------------------------

    subparser = parser_location.add_subparsers(dest='subcommand')

    loccre = subparser.add_parser('create',  help="Create a new location in the database")
    loccre.add_argument('--site-name',  type=str, nargs='+', required=True, help="Name identifying the place")
    loccre.add_argument('--location',   type=str, nargs='+', required=True, help="City/Town where the site belongs to")
    loccre.add_argument('--longitude',  type=float, default=None, required=True, help='Site longitude in decimal degrees, negative West')
    loccre.add_argument('--latitude',   type=float, default=None, required=True, help='Site latitude in decimal degrees, negative South')
    loccre.add_argument('--utc-offset', type=int,   default=0, help='**CAMERA UTC offset!** (if not set in UTC) GMT+1 = +1 ')

    return parser

# -------------------
# Applcation assembly
# -------------------

options = createParser().parse_args(sys.argv[1:])
startLogging(
	console  = options.console,
	filepath = options.log_file
)

application = service.Application("azotool")

dbaseService = DatabaseService(options.dbase, False)
dbaseService.setName(DatabaseService.NAME)
dbaseService.setServiceParent(application)

cmdService = CommandService(options)
cmdService.setName(CommandService.NAME)
cmdService.setServiceParent(application)

# Start the ball rolling
service.IService(application).startService()
reactor.run()
sys.exit(get_status_code())