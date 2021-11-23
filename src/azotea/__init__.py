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

# Access SQL scripts withing the package
from pkg_resources import resource_filename

# ---------------
# Twisted imports
# ---------------

from twisted  import __version__ as __twisted_version__

#--------------
# local imports
# -------------

from ._version import get_versions

# ----------------
# Module constants
# ----------------

FITS_HEADER_TYPE = 'FITS'
EXIF_HEADER_TYPE = 'EXIF'

DATE_SELECTION_ALL          = 'All'
DATE_SELECTION_DATE_RANGE   = 'Date range'
DATE_SELECTION_LATEST_NIGHT = 'Latest night'
DATE_SELECTION_LATEST_MONTH = 'Latest month'
DATE_SELECTION_PENDING      = 'Pending'

# -----------------------
# Module global variables
# -----------------------

__version__ = get_versions()['version']

name = os.path.split(os.path.dirname(sys.argv[0]))[-1]

VERSION_STRING = "{4} {0} on Twisted {1}, Python {2}.{3}".format(
		__version__, 
		__twisted_version__, 
		sys.version_info.major, 
		sys.version_info.minor,
		name)

# DATABASE RESOURCES
SQL_SCHEMA           = resource_filename(__name__, os.path.join('dbase', 'sql', 'schema.sql'))
SQL_INITIAL_DATA_DIR = resource_filename(__name__, os.path.join('dbase', 'sql', 'initial' ))
SQL_UPDATES_DATA_DIR = resource_filename(__name__, os.path.join('dbase', 'sql', 'updates' ))

del get_versions
del name
