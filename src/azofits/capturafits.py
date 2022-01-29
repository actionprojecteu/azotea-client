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

#--------------
# local imports
# -------------

from astropy.io import fits

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
    '''missing --model option in command line'''

class MissingBayerError(FITSBaseError):
    '''missing --bayer-pattern option in command line'''
   
class MissingDateObsError(FITSBaseError):
    '''missing DATE-OBS and file guessing failed'''

class MissingExptimeObsError(FITSBaseError):
    '''missing EXPTIME and file guessing failed'''

# -----------------------
# Module global variables
# -----------------------

log = logging.getLogger("azofits")

def fits_edit(filepath, swcreator, swcomment, model, bayer_pattern, gain, diameter, focal_length, x_pixsize, y_pixsize):
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
    if model is None:
        raise MissingModelError(filepath)
    if bayer_pattern is None:
        raise MissingBayerError(filepath)

    # Open FITS file and process headers
    with fits.open(filepath, mode='update') as hdul:
        header = hdul[0].header
        
        # Handle INSTRUME pattern        
        old_value = header.get('INSTRUME')
        if model is not None and old_value != model:
            header['INSTRUME'] = model
            header.comments['INSTRUME'] = "Camera model"
            header['HISTORY'] = f'Added/Changed INSTRUME from {old_value} to {model}'
       
        # Handling missing DATE-OBS
        old_value = header.get('DATE-OBS')
        if old_value is None and date_obs is None:
            raise MissingDateObsError(filepath)
        elif old_value is None and date_obs is not None:
            header['DATE-OBS'] = date_obs.strftime("%Y-%m-%dT%H:%M:%S")
            header['HISTORY'] = f'Added/Changed DATE from {old_value} to {date_obs}'
           
        # Handle EXPTIME pattern        
        old_value = header.get('EXPTIME')
        if old_value is None and exptime is None:
            raise MissingExptimeError(filepath)
        if old_value != exptime:
            header['EXPTIME'] = exptime
            header.comments['EXPTIME'] = "[s]"
            header['HISTORY'] = f'Added/Changed EXPTIME from {old_value} to {exptime}'
            header['HISTORY'] = f"Guessed DATE-OBS/EXPTIME from file name '{iso_basename}'"

        # Handle BAYERPAT        
        old_value = header.get('BAYERPAT')
        if  gain is not None and  old_value != bayer_pattern:
            header['BAYERPAT'] = bayer_pattern
            header.comments['BAYERPAT'] = "Top down convention. (0,0) is upper left"
            header['HISTORY'] = f'Added/Changed BAYERPAT from {old_value} to {bayer_pattern}'
        
        # Handling of LOG-GAIN
        old_value = header.get('LOG-GAIN')
        if gain is not None and  old_value != gain: 
            header['LOG-GAIN'] = gain
            header.comments['LOG-GAIN'] = 'Logarithmic gain in 0.1 dB units'
            header['HISTORY'] = f'Added/Changed LOG-GAIN from {old_value} to {gain}'

        # Handle APTDIA        
        old_value = header.get('APTDIA')
        if diameter is not None and old_value != diameter:
            header['APTDIA'] = diameter
            header['HISTORY'] = f'Added/Changed APTDIA from {old_value} to {diameter}'
            header.comments['APTDIA'] = "[mm]"

        # Handle FOCALLEN        
        old_value = header.get('FOCALLEN')
        if focal_length is not None and  old_value != focal_length:
            header['FOCALLEN'] = focal_length
            header['HISTORY'] = f'Added/Changed FOCALLEN from {old_value} to {focal_length}'
            header.comments['FOCALLEN'] = "[mm]"

        # Handle XPIXSZ        
        old_value = header.get('XPIXSZ')
        if x_pixsize is not None and old_value != x_pixsize:
            header['XPIXSZ'] = x_pixsize
            header['HISTORY'] = f'Added/Changed XPIXSZ from {old_value} to {x_pixsize}'
            header.comments['XPIXSZ'] = "[um]"

        # Handle YPIXSZ        
        old_value = header.get('YPIXSZ')
        if y_pixsize is not None and  old_value != y_pixsize:
            header['YPIXSZ'] = y_pixsize
            header['HISTORY'] = f'Added/Changed YPIXSZ from {old_value} to {y_pixsize}'
            header.comments['YPIXSZ'] = "[um]"

        # Handling of SWCREATE
        old_value = header.get('SWCREATE')
        if old_value != swcreator:
            header['SWCREATE'] = swcreator
            header.comments['SWCREATE'] = 'Updated on ' + now
            header['HISTORY'] = f'Added/Changed SWCREATE from {old_value} to {swcreator}'

        # Handling of SWMODIFY
        old_value = header.get('SWMODIFY')
        if old_value is None:
            header['SWMODIFY'] = 'azofits'
            header.comments['SWMODIFY'] = 'Updated on ' + now
            header['HISTORY'] = 'Added SWMODIFY'
