# ----------------------------------------------------------------------
# Copyright (c) 2020
#
# See the LICENSE file for details
# see the AUTHORS file for authors
# ----------------------------------------------------------------------

#--------------------
# System wide imports
# -------------------

import datetime

#--------------
# local imports
# -------------

# ----------------
# Module constants
# ----------------

# -----------------------
# Module global variables
# -----------------------

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

def mkbool(boolstr):
    result = None
    if boolstr == 'True':
        result = True
    elif boolstr == 'False':
        result = False
    return result

def mkdate(datestr):
    date = None
    for fmt in ['%Y-%m','%Y-%m-%d','%Y-%m-%dT%H:%M:%S','%Y-%m-%dT%H:%M:%SZ']:
        try:
            date = datetime.datetime.strptime(datestr, fmt)
        except ValueError:
            pass
    return date
