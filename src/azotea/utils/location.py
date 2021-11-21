# ----------------------------------------------------------------------
# Copyright (c) 2020
#
# See the LICENSE file for details
# see the AUTHORS file for authors
# ----------------------------------------------------------------------

#--------------------
# System wide imports
# -------------------

import math
import random

# -------------------
# Third party imports
# -------------------

#--------------
# local imports
# -------------

# ----------------
# Module constants
# ----------------

EARTH_RADIUS = 6371.0  # in Km

# -----------------------
# Module global variables
# -----------------------

# ------------------------
# Module Utility Functions
# ------------------------

def randomize(longitude, latitude, error_Km = 1.0):
    # Includes +- 1Km uncertainty in coordinates
    delta_long  = random.uniform(-error_Km, error_Km)*(1/EARTH_RADIUS)*math.cos(math.radians(latitude))
    delta_lat   = random.uniform(-error_Km, error_Km)*(1/EARTH_RADIUS)
    random_long = longitude + math.degrees(delta_long)
    random_lat  = latitude  + math.degrees(delta_lat)
    # 1 meter of precision means 0.00001 degrees of round-up errors ((0.001/R)*(180/pi))
    # (5 digits) but we add 2 extra decimals anyway as we see it in Google Maps
    return round(random_long,7), round(random_lat,7)
