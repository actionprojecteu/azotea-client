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
import os.path

# -------------------
# Third party imports
# -------------------

import exifread
import rawpy

#--------------
# local imports
# -------------

from azotea.error import TooDifferentValuesBiasError, NotPowerOfTwoErrorBiasError, UnsupportedCFAError
from azotea.utils import NAMESPACE, log

# ----------------
# Module constants
# ----------------

# -----------------------
# Module global variables
# -----------------------

BAYER_LETTER = ['B','G','R','G']

# -----------------------
# Module global variables
# -----------------------

# ------------------------
# Module Utility Functions
# ------------------------

def nearest_power_of_two(bias):
    if bias == 0:
        return 0, False
    warning = False
    N1 = math.log10(bias)/math.log10(2)
    N2 = int(round(N1,0))
    log.debug("N1 = {n1}, N2 = {n2}",n1=N1, n2=N2)
    nearest = 2**N2
    if (math.fabs(N1-N2) > 0.012):  # determinend empirically for bias=127
        warning = True
    return nearest, warning


def analyze_bias(levels):
    log.info("analyzing bias levels({levels})",levels=levels)
    global_bias = min(levels)
    if max(levels) - global_bias > 4:
        raise TooDifferentValuesBiasError(global_bias, levels, 4)
    tuples   = [nearest_power_of_two(bias) for bias in levels]
    log.debug("biases tuples = {tuples}",tuples=tuples)
    biases   = [item[0] for item in tuples]
    warnings = [item[1] for item in tuples]
    if any(warnings):
        raise NotPowerOfTwoErrorBiasError(global_bias, levels)
    global_bias = biases[0]
    log.info("global bias set to = {global_bias}",global_bias=global_bias)
    return global_bias
      


def image_analyze_exif(filename):
    extension = os.path.splitext(filename)[1]
    result = None
    with open(filename, 'rb') as f:
        exif = exifread.process_file(f, details=False)
    if not exif:
        log.warn('Could not open EXIF metadata from {file}',file=filename)
        return None
    model = str(exif.get('Image Model', None)).strip()
    warning = False
    with rawpy.imread(filename) as img:
        color_desc = img.color_desc.decode('utf-8')
        if color_desc != 'RGBG':
            raise UnsupporteCFAError(color_desc)
        bayer_pattern = ''.join([ BAYER_LETTER[img.raw_pattern[row,column]] for row in (1,0) for column in (1,0)])
        length, width = img.raw_image.shape    # Raw numbers, not divide by 2
        levels = img.black_level_per_channel
    try:
        bias = analyze_bias(levels)
    except NotPowerOfTwoErrorBiasError as e:
        bias = e.bias
        warning = str(e)
    except TooDifferentValuesBiasError as e:
        bias = e.bias
        warning = str(e)
    else:
        warning = None
    info = {
        'model'         : model,
        'extension'     : extension,
        'bias'          : bias,
        'width'         : width,
        'length'        : length,
        'header_type'   : 'EXIF',
        'bayer_pattern' : bayer_pattern,
    }
    log.debug("CAMERA SUMMARY INFO = {i}",i=info)
    return info, warning
