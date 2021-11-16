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

ICONS_DIR = resource_filename(__name__, os.path.join('gui', 'resources', 'img' ))
IMG_ROI     = resource_filename(__name__, os.path.join('gui', 'resources', 'img', 'roi.png'))

# About Widget resources configuration
ABOUT_DESC_TXT = resource_filename(__name__, os.path.join('gui', 'resources', 'about', 'descr.txt'))
ABOUT_ACK_TXT  = resource_filename(__name__, os.path.join('gui', 'resources', 'about', 'ack.txt'))
ABOUT_IMG      = resource_filename(__name__, os.path.join('gui', 'resources', 'about', 'azotea192.png'))
ABOUT_ICONS = (
	('Universidad Complutense de Madrid', resource_filename(__name__, os.path.join('gui', 'resources', 'about', 'ucm64.png'))),
	('GUAIX', resource_filename(__name__, os.path.join('gui', 'resources', 'about', 'guaix60.jpg'))),
	('ACTION PROJECT EU', resource_filename(__name__, os.path.join('gui', 'resources', 'about', 'action64.png'))),
)

# Consent form resources configuration

CONSENT_TXT = resource_filename(__name__, os.path.join('gui', 'resources', 'consent', 'descr.txt'))
CONSENT_UCM = resource_filename(__name__, os.path.join('gui', 'resources', 'about', 'ucm64.png'))

del get_versions
del name