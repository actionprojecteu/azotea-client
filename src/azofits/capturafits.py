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
import datetime
import logging

# ---------------------
# Third party libraries
# ---------------------

from astropy.io import fits

#--------------
# local imports
# -------------

from azofits.utils import SW_MODIFIER, SW_MODIFIER_COMMENT, fits_edit_keyword

# ----------------
# Module constants
# ----------------

# ----------
# Exceptions
# ----------

class FITSBaseError(Exception):
    def __str__(self):
        s = self.__doc__
        if self.args:
            s = ' {0}: {1}'.format(s, str(self.args[0]))
        s = '{0}.'.format(s)
        return s

class MissingGainError(FITSBaseError):
    '''missing --gain option in command line'''

class MissingModelError(FITSBaseError):
    '''missing --camera option in command line'''

class MissingBayerError(FITSBaseError):
    '''missing --bayer-pattern option in command line'''
   
class MissingDateObsError(FITSBaseError):
    '''missing DATE-OBS and file guessing failed'''

class MissingExptimeObsError(FITSBaseError):
    '''missing EXPTIME and file guessing failed'''

# -----------------------
# Module global variables
# -----------------------

log = logging.getLogger(SW_MODIFIER)

def fits_edit(filepath, swcreator, swcomment, camera, bias, bayer_pattern, gain, diameter, focal_length, x_pixsize, y_pixsize, image_type):
    basename = os.path.basename(filepath)
    now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')
    # Find the observation date from the file name !
    iso_basename = os.path.splitext(basename)[0] # Strips the extension off
    date_obs, exptime = os.path.splitext(iso_basename)
    try:
        date_obs = datetime.datetime.strptime(date_obs, '%Y%m%d-%H%M%S')
        exptime  = float(exptime[1:]) * 1.0e-3   # From milliseconds to seconds
    except Exception as e:
        log.critical(str(e))
        date_obs = None
        exptime  = None
    if gain is None:
        raise MissingGainError(filepath)
    if camera is None:
        raise MissingModelError(filepath)
    if bayer_pattern is None:
        raise MissingBayerError(filepath)

    # Open FITS file and process headers
    with fits.open(filepath, mode='update') as hdul:
        header = hdul[0].header
        header['HISTORY'] = f"Logging {SW_MODIFIER} changes on {now}"

        fits_edit_keyword(
            header    = header,
            keyword   = 'SWCREATE',
            new_value = swcreator,
            comment   = swcomment
        )

        fits_edit_keyword(
            header    = header,
            keyword   = 'SWMODIFY',
            new_value = SW_MODIFIER,
            comment   = SW_MODIFIER_COMMENT
        )

        fits_edit_keyword(
            header    = header,
            keyword   = 'INSTRUME',
            new_value = camera,
            comment   = "Camera model"
        )

        fits_edit_keyword(
            header    = header,
            keyword   = 'IMAGETYP',
            new_value = image_type,
        )

        fits_edit_keyword(
            header    = header,
            keyword   = 'PEDESTAL',
            new_value = bias,
            comment   = 'Substract this value to get zero-based ADUs'
        )

        fits_edit_keyword(
            header    = header,
            keyword   = 'BAYERPAT',
            new_value = bayer_pattern,
            comment   = 'Top down convention. (0,0) is upper left'
        )

        fits_edit_keyword(
            header    = header,
            keyword   = 'LOG-GAIN',
            new_value = gain,
            comment   = 'Logarithmic gain in 0.1 dB units'
        )

        fits_edit_keyword(
            header    = header,
            keyword   = 'APTDIA',
            new_value = diameter,
            comment   = '[mm]'
        )

        fits_edit_keyword(
            header    = header,
            keyword   = 'FOCALLEN',
            new_value = focal_length,
            comment   = '[mm]'
        )

        fits_edit_keyword(
            header    = header,
            keyword   = 'XPIXSZ',
            new_value = x_pixsize,
            comment   = '[um]'
        )

        fits_edit_keyword(
            header    = header,
            keyword   = 'YPIXSZ',
            new_value = x_pixsize,
            comment   = '[um]'
        )

        # Handling missing DATE-OBS
        # new DATE-OBS value taken from file name
        old_value = header.get('DATE-OBS')
        if old_value is None and date_obs is None:
            raise MissingDateObsError(filepath)
        elif old_value is None and date_obs is not None:
            header['DATE-OBS'] = date_obs.strftime("%Y-%m-%dT%H:%M:%S")
            header['HISTORY'] = f'Added/Changed DATE from {old_value} to {date_obs}'
           
        # Handle missing EXPTIME pattern  
        # new EXPTIME value taken from file name      
        old_value = header.get('EXPTIME')
        if old_value is None and exptime is None:
            raise MissingExptimeError(filepath)
        if old_value != exptime:
            header['EXPTIME'] = exptime
            header.comments['EXPTIME'] = "[s]"
            header['HISTORY'] = f'Added/Changed EXPTIME from {old_value} to {exptime}'
            header['HISTORY'] = f"Guessed DATE-OBS/EXPTIME from file name '{iso_basename}'"
