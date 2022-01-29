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
from astropy.io import fits 

#--------------
# local imports
# -------------

from azotea.utils.fits import fits_assert_valid, fits_check_valid_extension

# ----------------
# Module constants
# ----------------

BAYER_LETTER = ['B','G','R','G']

BAYER_PTN_LIST = ('RGGB', 'BGGR', 'GRBG', 'GBRG')

# -----------------------
# Module global variables
# -----------------------

# -----------------------
# Module global variables
# -----------------------

# ----------
# Exceptions
# ----------


class UnsupportedCFAError(ValueError):
    '''Unsupported Color Filter Array type'''
    def __str__(self):
        s = self.__doc__
        if self.args:
            s = ' {0}: {1}'.format(s, str(self.args[0]))
        s = '{0}.'.format(s)
        return s


class BiasError(ValueError):
    '''Value differs much from power of two'''
    def __init__(self, bias, levels, *args):
        self.bias = bias
        self.levels = levels

    def __str__(self):
        s = self.__doc__
        if self.args:
            s = ' {0}: {1} '.format(s, self.args[0], self.levels)
        s = '{0}.'.format(s)
        return s


class NotPowerOfTwoErrorBiasError(BiasError):
    '''Value differs much from a power of two'''
    pass
 

class TooDifferentValuesBiasError(BiasError):
    '''Differences in counts between channels exceed threshold'''
    pass

# ------------------------
# Module Utility Functions
# ------------------------

def image_analyze(filepath):
    extension = os.path.splitext(filepath)[1]
    if fits_check_valid_extension(extension):
        return image_analyze_fits(filepath)
    else:
        return image_analyze_exif(filepath)

# -------------
# FITS analysis
# -------------

def image_analyze_fits(filepath):
    extension = os.path.splitext(filepath)[1]
    warning = False
    with fits.open(filepath, memmap=False) as hdu_list:
        header        = hdu_list[0].header
        fits_assert_valid(filepath, header)
        width         = header['NAXIS1']
        length        = header['NAXIS2']
        # This assumes SharpCap software for the time being
        model         = header['INSTRUME']
        bayer_pattern = header['BAYERPAT']
    info = {
        'model'         : model,
        'extension'     : extension,
        'bias'          : 0,
        'width'         : width,
        'length'        : length,
        'header_type'   : 'FITS',
        'bayer_pattern' : bayer_pattern,
    }
    return info, warning


# --------------------
# EXIF header analysis
# --------------------

def nearest_power_of_two(bias):
    if bias == 0:
        return 0, False
    warning = False
    N1 = math.log10(bias)/math.log10(2)
    N2 = int(round(N1,0))
    #log.debug("N1 = {n1}, N2 = {n2}",n1=N1, n2=N2)
    nearest = 2**N2
    if (math.fabs(N1-N2) > 0.012):  # determinend empirically for bias=127
        warning = True
    return nearest, warning


def analyze_bias(levels):
    #log.info("analyzing bias levels({levels})",levels=levels)
    global_bias = min(levels)
    if max(levels) - global_bias > 4:
        raise TooDifferentValuesBiasError(global_bias, levels, 4)
    tuples   = [nearest_power_of_two(bias) for bias in levels]
    #log.debug("biases tuples = {tuples}",tuples=tuples)
    biases   = [item[0] for item in tuples]
    warnings = [item[1] for item in tuples]
    if any(warnings):
        raise NotPowerOfTwoErrorBiasError(global_bias, levels)
    global_bias = biases[0]
    #log.info("global bias set to = {global_bias}",global_bias=global_bias)
    return global_bias
      

def image_analyze_exif(filepath):
    extension = os.path.splitext(filepath)[1]
    with open(filepath, 'rb') as f:
        exif = exifread.process_file(f, details=False)
    # This ensures that non EXIF images are detected and an exeption is raised
    if not exif:
        message = 'Could not open EXIF metadata'
        raise ValueError(message)
    model = str(exif.get('Image Model', None)).strip()
    with rawpy.imread(filepath) as img:
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
        warning = False
    info = {
        'model'         : model,
        'extension'     : extension,
        'bias'          : bias,
        'width'         : width,
        'length'        : length,
        'header_type'   : 'EXIF',
        'bayer_pattern' : bayer_pattern,
    }
    #log.debug("CAMERA SUMMARY INFO = {i}",i=info)
    return info, warning
