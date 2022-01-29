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
import logging

#--------------
# local imports
# -------------

from astropy.io import fits

# ----------------
# Module constants
# ----------------

# -----------------------
# Module global variables
# -----------------------

log = logging.getLogger("azofits")

def fits_edit(filepath, swcreator, swcomment, model, image_type, bayer_pattern, gain, x_pixsize, y_pixsize):
	basename = os.path.basename(filepath)
	with fits.open(filepath, mode='update') as hdul:
		header = hdul[0].header
