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
import logging
import traceback
import importlib

#--------------
# local imports
# -------------

from azotea import __version__
from azofits.utils import IMAGE_TYPES, SW_CREATORS, SW_MODIFIER, fits_image_type, fits_swcreator

from azotea.utils.camera import BAYER_PTN_LIST


# ----------------
# Module constants
# ----------------

LOG_CHOICES     = ('critical', 'error', 'warn', 'info', 'debug')

# -----------------------
# Module global variables
# -----------------------

log = logging.getLogger('azoplot')

# ----------
# Exceptions
# ----------


# ------------------------
# Module utility functions
# ------------------------

def configureLogging(options):
    if options.verbose:
        level = logging.DEBUG
    elif options.quiet:
        level = logging.WARN
    else:
        level = logging.INFO
    
    log.setLevel(level)
    # Log formatter
    #fmt = logging.Formatter('%(asctime)s - %(name)s [%(levelname)s] %(message)s')
    fmt = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
    # create console handler and set level to debug
    if options.console:
        ch = logging.StreamHandler()
        ch.setFormatter(fmt)
        ch.setLevel(level)
        log.addHandler(ch)
    # Create a file handler suitable for logrotate usage
    if options.log_file:
        #fh = logging.handlers.WatchedFileHandler(options.log_file)
        fh = logging.handlers.TimedRotatingFileHandler(options.log_file, when='midnight', interval=1, backupCount=365)
        fh.setFormatter(fmt)
        fh.setLevel(level)
        log.addHandler(fh)

def validfile(path):
    if not os.path.isfile(path):
        raise IOError(f"Not valid or existing file: {path}")
    return path

def validdir(path):
    if not os.path.isdir(path):
        raise IOError(f"Not valid or existing directory: {path}")
    return path

           
# -----------------------
# Module global functions
# -----------------------

def createParser():
    # create the top-level parser
    name = os.path.split(os.path.dirname(sys.argv[0]))[-1]
    parser    = argparse.ArgumentParser(prog=name, description='FITS batch editor for AZOTEA')

    # Global options
    parser.add_argument('--version', action='version', version='{0} {1}'.format(name, __version__))
    parser.add_argument('-c', '--console', action='store_true',  help='log to console.')
    parser.add_argument('-l', '--log-file', type=str, default=None, action='store', metavar='<file path>', help='log to file')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-v', '--verbose', action='store_true', help='Verbose logging output.')
    group.add_argument('-q', '--quiet',   action='store_true', help='Quiet logging output.')


    # --------------------------
    # Create first level parsers
    # --------------------------

    subparser = parser.add_subparsers(dest='command')

    parser_image  = subparser.add_parser('image', help='image command')
    
    # ---------------------------------------
    # Create second level parsers for 'image'
    # ---------------------------------------

    subparser = parser_image.add_subparsers(dest='subcommand')
    iplot = subparser.add_parser('stats',  help="Plot image stats")
    group = iplot.add_mutually_exclusive_group(required=True)
    group.add_argument('-d', '--images-dir', type=validdir, action='store', metavar='<path>', help='Images directory')
    group.add_argument('-f', '--image-file', type=validfile, action='store', metavar='<path>', help='single FITS file path')  
    iplot.add_argument('-x','--width',  type=int, default=500, help="Region of interest width [pixels].")
    iplot.add_argument('-y','--height', type=int, default=400, help="Region of interest height [pixels].")
    iplot.add_argument('-b','--bayer', choices=BAYER_PTN_LIST, default=None, help='Bayer pattern layout')

    return parser

   

# ================ #
# MAIN ENTRY POINT #
# ================ #

def main():
    '''
    Utility entry point
    '''
    try:
        options = createParser().parse_args(sys.argv[1:])
        configureLogging(options)
        name = os.path.split(os.path.dirname(sys.argv[0]))[-1]
        log.info(f"============== {name} {__version__} ==============")
        package = f"{name}"
        command  = f"{options.command}"
        subcommand = f"{options.subcommand}"
        try: 
            command = importlib.import_module(command, package=package)
        except ModuleNotFoundError: # when debugging module in git source tree ...
            command  = f".{options.command}"
            command = importlib.import_module(command, package=package)
        getattr(command, subcommand)(options)
    except KeyboardInterrupt as e:
        log.critical("[%s] Interrupted by user ", __name__)
    except Exception as e:
        traceback.print_exc()
        log.critical("[%s] Fatal error => %s", __name__, str(e) )
    finally:
        pass

main()
