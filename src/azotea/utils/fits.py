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
import re 

#--------------
# local imports
# -------------

# ----------------
# Module constants
# ----------------

GAIN_REGEXP = re.compile(r'Gain=(\d+)')

# -----------------------
# Module global variables
# -----------------------

# Allowed FITS writters by azotea-client

FITS_WRITTERS = ('SharpCap',)

FITS_EXTENSIONS = ('.fit', '.fits', '.fts')


# ----------
# Exceptions
# ----------

class UnsupportedFITSFormat(ValueError):
    '''Unsupported FITS Format'''
    def __str__(self):
        s = self.__doc__
        if self.args:
            s = ' {0}: {1}'.format(s, str(self.args[0]))
        s = '{0}.'.format(s)
        return s


# ------------------------
# Module Utility Functions
# ------------------------

def check_fits_file(extension):
    return extension.lower() in FITS_EXTENSIONS

def check_fits_writter(header):
    # This is heuristic
    software = header.get('SWCREATE', None)
    if software not in FITS_WRITTERS:
        raise UnsupportedFITSFormat(f"FITS Image was not taken by one of these programs: {ALLOWED_FITS_WRITTERS}")
    return software

def check_fits_gain(filepath):
    '''Heuristic search for additional parameyter not in FITS header, written by SharpCap'''
    basename = os.path.basename(filepath)
    basename = os.path.splitext(basename)[0] # Strips the extension off
    dirname = os.path.dirname(filepath)
    metadata_file = os.path.join(dirname, basename + '.CameraSettings.txt')
    with open(metadata_file,'r') as fd:
        for line in fd.readlines():
            matchobj = GAIN_REGEXP.search(line)
            if matchobj:
                gain = int(matchobj.group(1))
                return gain
    return None

