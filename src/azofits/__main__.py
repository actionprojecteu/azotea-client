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
import glob
import argparse
import logging
import traceback

from astropy.io import fits


#--------------
# local imports
# -------------

from azotea import __version__
from azotea.utils.camera import BAYER_PTN_LIST

# ----------------
# Module constants
# ----------------

LOG_CHOICES = ('critical', 'error', 'warn', 'info', 'debug')
IMAGE_TYPES = ('LIGHT', 'BIAS', 'DARK', 'FLAT')
EXTENSIONS  = ('*.fit', '*.FIT', '*.fits', '*.FITS', '*.fts', '*.FTS')

# Mapping between command line name and FITS header name in SWCREATE

SW_CREATORS = {
    'SharpCap'    : ('SharpCap', None),
    'captura-fits': ('captura-fits', 'captura-fits (C) Alberto Castellon'),
}

SW_MODIFIER = 'azofits'

# -----------------------
# Module global variables
# -----------------------

log = logging.getLogger("azofits")

# ----------
# Exceptions
# ----------
from azofits.sharpcap import MissingGainError

class UnknownSoftwareCreatorError(Exception):
    '''Unknown FITS software creator'''
    def __str__(self):
        s = self.__doc__
        if self.args:
            s = ' {0}: {1}'.format(s, str(self.args[0]))
        s = '{0}.'.format(s)
        return s

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


def scan_non_empty_dirs(root, depth=None):
    '''Returns a list of non empty dirs under root dir'''
    if os.path.basename(root) == '':
        root = root[:-1]
    dirs = [dirpath for dirpath, dirs, files in os.walk(root) if files]
    dirs.append(root)   # Add it for images just under the root folder
    if depth is None:
        return dirs 
    L = len(root.split(sep=os.sep))
    return list(filter(lambda d: len(d.split(sep=os.sep)) - L <= depth, dirs))


def fits_switcher(filepath, swcreator, swcomment, options):
    if swcreator == 'SharpCap':
        from azofits.sharpcap import fits_edit
    elif swcreator == 'captura-fits':
        from azofits.capturafits import fits_edit
    fits_edit(
        filepath      = filepath,
        swcreator     = swcreator, 
        swcomment     = swcomment,
        camera        = ' '.join (options.camera) if options.camera else None,
        bias          = options.bias,
        bayer_pattern = options.bayer_pattern,
        gain          = options.gain,
        x_pixsize     = options.x_pixsize,
        y_pixsize     = options.y_pixsize,
        diameter      = options.diameter,
        focal_length  = options.focal_length,
    )

def process_fits_files(directories, options):
    for directory in directories:
        paths_set = set()
        for extension in EXTENSIONS:
            alist  = glob.glob(os.path.join(directory, extension))
            paths_set  = paths_set.union(alist)
        N = len(paths_set)
        if N:
            log.warning(f"Scanning directory '{directory}'. Found {N} FITS images matching '{EXTENSIONS}'")
        for i, filepath in enumerate(sorted(paths_set), start=1):
            try:
                basename = os.path.basename(filepath)
                with fits.open(filepath) as hdul:
                    header = hdul[0].header
                    swmodify = header.get('SWMODIFY')
                    if swmodify == 'azofits':
                        if options.quiet:
                            if (i % 50 == 0):
                                log.warning(f"Skipping edited '{basename}' [{i}/{N}] ({100*i//N}%).")
                        else:
                            log.info(f"Skipping edited '{basename}' [{i}/{N}] ({100*i//N}%).")
                        continue    # Already been processed
                    if options.quiet:
                        if (i % 50 == 0):
                            log.warning(f"Editing '{basename}' [{i}/{N}] ({100*i//N}%).")
                    else:
                        log.info(f"Editing '{basename}' [{i}/{N}] ({100*i//N}%).")
                    swcreator = header.get('SWCREATE')
                    if swcreator is None and options.swcreator is None:
                        raise UnknownSoftwareCreatorError("Missing --swcreator option?")
                    elif swcreator is None and options.swcreator is not None:
                        swcreator, swcomment = SW_CREATORS[options.swcreator]
                        hdul.close()
                        fits_switcher(filepath, swcreator, swcomment, options)
                    elif swcreator is not None and options.swcreator is None:
                        swcomment = header.comments['SWCREATE']
                        hdul.close()
                        fits_switcher(filepath, swcreator, swcomment, options)
                    else:
                        if swcreator != options.swcreator:
                            log.warning(f"Not editing '{basename}': Existing FITS SWCREATE value ({swcreator}) does not match --swcreate option ({options.swcreator})")
                            continue
            except (FileNotFoundError, MissingGainError) as e:
                log.critical("[%s] Fatal error => %s", __name__, str(e) )
                continue

            except Exception as e:
                raise e

# -----------------------
# Module global functions
# -----------------------


def createParser():
    # create the top-level parser
    name = os.path.split(os.path.dirname(sys.argv[0]))[-1]
    parser    = argparse.ArgumentParser(prog=name, description='FITS batch editor for AZOTEA')

    # Global options
    parser.add_argument('--version', action='version', version='{0} {1}'.format(name, __version__))
    parser.add_argument('-d', '--images-dir', type=str, required=True, action='store', metavar='<file path>', help='Base directory to edit FITS files')
    
    # Logging options
    parser.add_argument('-c', '--console', action='store_true',  help='log to console.')
    parser.add_argument('-l', '--log-file', type=str, default=None, action='store', metavar='<file path>', help='log to file')
    group1 = parser.add_mutually_exclusive_group()
    group1.add_argument('-v', '--verbose', action='store_true', help='Verbose logging output.')
    group1.add_argument('-q', '--quiet',   action='store_true', help='Quiet logging output.')

    # FITS specific editing info    
    parser.add_argument('--swcreator', choices=SW_CREATORS.keys(), default=None, action='store', help='Name of software that created the FITS files')
    parser.add_argument('--camera',     type=str, nargs='+', default=None, help="Camera model")
    parser.add_argument('--bayer-pattern', choices=BAYER_PTN_LIST, default=None, help='Bayer pattern layout')
    parser.add_argument('--gain',      type=float, default=None, help="CMOS detector GAIN settings")
    parser.add_argument('--bias',      type=int,   default=0,    help="Global Bias for every image")
    parser.add_argument('--x-pixsize', type=float, default=None, help="Pixel width in um.")
    parser.add_argument('--y-pixsize', type=float, default=None, help="Pixel height in um.")
    #parser.add_argument('--image-type', choices=IMAGE_TYPES,  default=None, help='Image type')
    parser.add_argument('--diameter', type=float,  default=None, help='Optics diameter in mm')
    parser.add_argument('--focal-length', type=float,  default=None, help='Focal length in mm')

   
    return parser


# -------------------
# Booting application
# -------------------


def main():
    '''
    Utility entry point
    '''
    try:
        options = createParser().parse_args(sys.argv[1:])
        configureLogging(options)
        log.info("=============== AZOTEA FITS EDITOR {0} ===============".format(__version__))
        directories = scan_non_empty_dirs(options.images_dir)
        process_fits_files(directories, options)
    except KeyboardInterrupt as e:
        log.critical("[%s] Interrupted by user ", __name__)
    except Exception as e:
        log.critical("[%s] Fatal error => %s", __name__, str(e) )
        traceback.print_exc()
    finally:
        pass

main()
