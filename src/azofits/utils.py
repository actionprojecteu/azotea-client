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

# ---------------
# Twisted imports
# ---------------

#--------------
# local imports
# -------------

# ----------------
# Module constants
# ----------------

# -----------------------
# Module global variables
# -----------------------

SW_MODIFIER = 'azofits'
SW_MODIFIER_COMMENT = f"UCM's {SW_MODIFIER} utility for the AZOTEA project"

# Mapping from command line arguments
# to FITS keyword values
IMAGE_TYPES_MAPPING = {
    'bias' : 'Bias Frame',
    'dark' : 'Dark Frame',
    'flat' : 'Flat Frame',
    'mono' : 'Light Frame',
    'color': 'Tricolor Image',
}

IMAGE_TYPES = IMAGE_TYPES_MAPPING.keys()

# Mapping between command line name and FITS header name in SWCREATE
SW_CREATORS_MAPPTING = {
    'SharpCap'    : ('SharpCap', None),
    'captura-fits': ('captura-fits', 'captura-fits (C) Alberto Castellon'),
}

SW_CREATORS = SW_CREATORS_MAPPTING.keys()

# ------------------------
# Module utility functions
# ------------------------

def fits_image_type(image_tyoe):
    return IMAGE_TYPES_MAPPING.get(image_tyoe)

def fits_swcreator(swcreator):
    return SW_CREATORS_MAPPTING.get(swcreator)

def fits_edit_keyword(header, keyword, new_value, comment=None):
    old_value = header.get(keyword)
    change = new_value is not None and old_value != new_value
    if change:
        header[keyword] = new_value
        if comment:
            header.comments[keyword] = comment
            header['HISTORY'] = f'Added/Changed {keyword} from {old_value} to {new_value}'
    return change