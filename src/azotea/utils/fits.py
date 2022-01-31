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

FITS_EXTENSIONS = ('.fit', '.fits', '.fts')

# -----------------------
# Module global variables
# -----------------------

# ----------
# Exceptions
# ----------

class InvalidFITSError(Exception):
    '''FITS Image was not preprocessed by "azofits"'''
    def __str__(self):
        s = self.__doc__
        if self.args:
            s = ' {0}: {1}'.format(s, str(self.args[0]))
        s = '{0}.'.format(s)
        return s

# ------------------------
# Module Utility Functions
# ------------------------

def fits_check_valid_extension(extension):
    return extension.lower() in FITS_EXTENSIONS

def fits_assert_valid(filepath, header):
    # This is heuristic
    software = header.get('SWMODIFY')
    if software != 'azofits':
        raise InvalidFITSError(os.path.basename(filepath))
    return software
