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
from azotea.utils import get_status_code, mkdate
from azotea.logger  import startLogging
from azotea.dbase.service import DatabaseService
from azotool.cli.service import CommandService

import azotea.consent.form

# ----------------
# Module constants
# ----------------

LOG_CHOICES = ('critical', 'error', 'warn', 'info', 'debug')

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

    parser_consent  = subparser.add_parser('consent', help='consent command')
    parser_observer  = subparser.add_parser('observer', help='observer commands')
    parser_location  = subparser.add_parser('location', help='location commands')
    parser_camera   = subparser.add_parser('camera', help='camera commands')
    parser_roi    = subparser.add_parser('roi', help='roi commands')
    parser_misc = subparser.add_parser('configure', help='miscelanea commands')
    parser_sky  = subparser.add_parser('sky', help='sky background commands')
   
    # -----------------------------------------
    # Create second level parsers for 'consent'
    # -----------------------------------------

    subparser = parser_consent.add_subparsers(dest='subcommand')

    conform = subparser.add_parser('view',  help="View consent form")
    conform.add_argument('--agree',    action='store_true', help='Auto-agree conset form')
    
    # ------------------------------------------
    # Create second level parsers for 'observer'
    # ------------------------------------------

    subparser = parser_observer.add_subparsers(dest='subcommand')

    obscre = subparser.add_parser('create',  help="Create a new observer in the database")
    obscre.add_argument('--default',     action='store_true', help='Set this observer as the default observer')
    obscre.add_argument('--name',        type=str, nargs='+', required=True, help="Observer's name")
    obscre.add_argument('--surname',     type=str, nargs='+', required=True, help="Observer's surname")
    obscre.add_argument('--affiliation', type=str, nargs='+', required=True, help='Complete affiliation name')
    obscre.add_argument('--acronym',     type=str, nargs='+', required=True, help='Affiliation acronym')
    
    # ------------------------------------------
    # Create second level parsers for 'location'
    # ------------------------------------------

    subparser = parser_location.add_subparsers(dest='subcommand')

    loccre = subparser.add_parser('create',  help="Create a new location in the database")
    loccre.add_argument('--default',     action='store_true', help='Set this location as the default location')
    loccre.add_argument('--site-name',  type=str, nargs='+', required=True, help="Name identifying the place")
    loccre.add_argument('--location',   type=str, nargs='+', required=True, help="City/Town where the site belongs to")
    loccre.add_argument('--longitude',  type=float, default=None, help='Site longitude in decimal degrees, negative West')
    loccre.add_argument('--latitude',   type=float, default=None, help='Site latitude in decimal degrees, negative South')
    loccre.add_argument('--utc-offset', type=int,   default=0, help='**CAMERA UTC offset!** (if not set in UTC) GMT+1 = +1 ')
    loccre.add_argument('--randomize',  action='store_true', default=False, help='randomize a bit the geographical coordinates')

    # ----------------------------------------
    # Create second level parsers for 'camera'
    # ----------------------------------------
   
    subparser = parser_camera.add_subparsers(dest='subcommand')

    camcre = subparser.add_parser('create',  help="Create a new camera in the database")
    camcre.add_argument('--default',     action='store_true', help='Set this camera as the default camera')
    group = camcre.add_mutually_exclusive_group(required=True)
    group.add_argument('--from-image',  type=str, default=None, action='store', metavar='<image file path>', help='create camera by inspecting an image')
    group.add_argument('--as-given',    action='store_true', help='create camera by adding further parameters')
    # additional argumnets with the --as-given option
    camcre.add_argument('--model',       type=str, nargs='+', default=None, help="Camera Model (taken from EXIF data)")
    camcre.add_argument('--bias',        type=int, default=None, help="default bias, to be replicated in all channels if we cannot read ir from EXIF")
    camcre.add_argument('--extension',   type=str, default=None, help='File extension procuced by a camera (i.e. .NEF)')
    camcre.add_argument('--header-type', choices=('EXIF', 'FITS'), default=None,  help="Either 'EXIF' or 'FITS'")
    camcre.add_argument('--bayer-pattern', choices=('RGGB', 'BGGR','GRGB','GBGR'), default=None, help='Bayer pattern grid')
    camcre.add_argument('--width',        type=int, default=0, help="Number of raw columns, with no debayering")
    camcre.add_argument('--length',       type=int, default=0, help="Number of raw rows, with no debayering")

    # -------------------------------------
    # Create second level parsers for 'roi'
    # -------------------------------------

    subparser = parser_roi.add_subparsers(dest='subcommand')

    roicre = subparser.add_parser('create',  help="Create a new region of interest in the database")
    group = roicre.add_mutually_exclusive_group(required=True)
    roicre.add_argument('--default',     action='store_true', help='Set this ROI as the default ROI')
    group.add_argument('--from-image',  type=str, default=None, action='store', metavar='<image file path>', help='create camera by inspecting an image')
    group.add_argument('--as-given',    action='store_true', help='create camera by adding further parameters')
    # additional argumnets with the --from-image option
    roicre.add_argument('--width',   type=int, default=None, help="Width of central rectangle")
    roicre.add_argument('--height',  type=int, default=None, help="height of central rectangle")
    # additional argumnets with the --as-given option
    roicre.add_argument('--x1',      type=int, default=None, help="Starting pixel column")
    roicre.add_argument('--y1',      type=int, default=None, help="Starting pixel row")
    roicre.add_argument('--x2',      type=int, default=None, help='Ending pixel column')
    roicre.add_argument('--y2',      type=int, default=None, help="Ending pixel row")
    roicre.add_argument('--comment', type=str, nargs='+', default=None, help="Additional region comment")

    # ------------------------------------------
    # Create second level parsers for 'sky'
    # ------------------------------------------

    subparser = parser_sky.add_subparsers(dest='subcommand')

    skyexp = subparser.add_parser('export',  help="Export to CSV")
    skyexp.add_argument('--csv-dir', type=str, required=True, action='store', metavar='<csv directory>', help='directory where to place CSV files')
    group = skyexp.add_mutually_exclusive_group(required=True)
    group.add_argument('--latest-month', action='store_true', help='Latest month in database')
    group.add_argument('--latest-night', action='store_true', help='Latest night in database')
    group.add_argument('--all',          action='store_true', help='Export all nights')
    group.add_argument('--pending',      action='store_true', help='Export observations not yet published to server')
    group.add_argument('--range',        action='store_true', help='Export a date range')
    # options for range export
    skyexp.add_argument('--from-date', type=mkdate, default=None, metavar='<YYYY-MM-DD>', help="Start date in range")
    skyexp.add_argument('--to-date',   type=mkdate, default=None, metavar='<YYYY-MM-DD>', help='End date in range')

    # --------------------------------------------
    # Create second level parsers for 'configure'
    # --------------------------------------------

    subparser = parser_misc.add_subparsers(dest='subcommand')

    miscopt = subparser.add_parser('optics',  help="Create the 'optics' section in the configuration")
    miscopt.add_argument('--focal-length',   type=int, required=True, help='Camera focal length in mm.')
    miscopt.add_argument('--f-number',       type=str, required=True, help="Camera f/ ratio")

    pubcre = subparser.add_parser('publishing',  help="create the 'publishing' section in the configuration")
    pubcre.add_argument('--username', type=str, required=True, help="Server username")
    pubcre.add_argument('--password', type=str, required=True, help="Server password")
    pubcre.add_argument('--url',      type=str, default=None, help="Server URL")

    logcnf = subparser.add_parser('logging',  help="create the 'publishing' section in the configuration")
    logcnf.add_argument('--load',   type=str, choices=LOG_CHOICES, default=None, help="Image loading log level")
    logcnf.add_argument('--sky',        type=str, choices=LOG_CHOICES, default=None, help="Sky processing log level")
    logcnf.add_argument('--publish', type=str, choices=LOG_CHOICES, default=None, help="Publishing log level")
   
    return parser


def handle_agreement(options):
    connection = azotea.consent.form.get_database_connection(options.dbase)
    if options.command == 'consent' and options.subcommand == 'view':
        accepted = azotea.consent.form.check_agreement(connection)
        if accepted:
            print("-"*26)
            print("Agreement already accepted")
            print("-"*26)
            sys.exit(0)
        else:
            accepted = azotea.consent.form.view()
            if accepted:
                azotea.consent.form.save_agreement(connection)
                print("-"*18)
                print("Agreement accepted")
                print("-"*18)
                sys.exit(0)
            else:
                print("-"*22)
                print("Agreement not accepted")
                print("-"*22)
                sys.exit(126)
    else:
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