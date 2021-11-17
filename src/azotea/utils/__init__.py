# ----------------------------------------------------------------------
# Copyright (c) 2020
#
# See the LICENSE file for details
# see the AUTHORS file for authors
# ----------------------------------------------------------------------

#--------------------
# System wide imports
# -------------------

# ---------------
# Twisted imports
# ---------------

from twisted.logger   import Logger

#--------------
# local imports
# -------------

# ----------------
# Module constants
# ----------------

NAMESPACE = 'CTRL '

# -----------------------
# Module global variables
# -----------------------

log = Logger(namespace=NAMESPACE)

# Assume bad result unless we set it to ok
_exit_status_code = 1

# ------------------------
# Module Utility Functions
# ------------------------

def get_status_code():
    return _exit_status_code


def set_status_code(code):
    global _exit_status_code
    _exit_status_code = code


def chop(string, sep=None):
    '''Chop a list of strings, separated by sep and 
    strips individual string items from leading and trailing blanks'''
    chopped = [ elem.strip() for elem in string.split(sep) ]
    if len(chopped) == 1 and chopped[0] == '':
    	chopped = []
    return chopped


