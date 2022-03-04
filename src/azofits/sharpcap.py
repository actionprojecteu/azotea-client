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
import re
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

GAIN_REGEXP = re.compile(r'Gain=(\d+)')

# -----------------------
# Module global variables
# -----------------------

log = logging.getLogger(SW_MODIFIER)

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
    '''SharpCap did not provide any gain value in metadata'''

# -------------------------
# Module auxiliar functions
# -------------------------

def _fits_read_gain(filepath):
    '''Heuristic search for additional gain parameter not in FITS header, written by SharpCap'''
    basename = os.path.basename(filepath)
    basename = os.path.splitext(basename)[0] # Strips the extension off
    dirname = os.path.dirname(filepath)
    metadata_file = os.path.join(dirname, basename + '.CameraSettings.txt')
    with open(metadata_file,'r') as fd:
        for line in fd.readlines():
            matchobj = GAIN_REGEXP.search(line)
            if matchobj:
                gain = int(matchobj.group(1))
                return gain
    raise MissingGainError(basename)

# --------------------
# Module main function
# --------------------

def fits_edit(filepath, swcreator, swcomment, camera, bias, bayer_pattern, gain, 
    diameter, focal_length, x_pixsize, y_pixsize, image_type, comment):
    basename = os.path.basename(filepath)
    now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')
    if gain is None:
        gain = _fits_read_gain(filepath)

    with fits.open(filepath, mode='update') as hdul:
        header = hdul[0].header
        header['HISTORY'] = f"Logging {SW_MODIFIER} changes on {now}"

        fits_edit_keyword(
            header    = header,
            keyword   = 'SWMODIFY',
            new_value = SW_MODIFIER,
            comment   = SW_MODIFIER_COMMENT
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
       
        # Handling of excessive seconds decimals in DATE-OBS
        tstamp = header['DATE-OBS']
        if len(tstamp) > 26:
            tstamp = tstamp[0:26]
            header['DATE-OBS'] = tstamp
            header['HISTORY']  = 'Fixed excessive decimals (>6) in DATE-OBS'

        # handling old Style BAYOFFX, BAYOFFY keywords
        bayoffx = header.get('BAYOFFX')
        if bayoffx is not None:
            header['XBAYROFF'] = bayoffx
            del header['BAYOFFX']
            header['HISTORY'] = 'Substituted keyword BAYOFFX -> XBAYROFF'
        bayoffy = header.get('BAYOFFY')
        if bayoffy is not None:
            header['YBAYROFF'] = bayoffy
            del header['BAYOFFY']
            header['HISTORY'] = 'Substituted keyword BAYOFFY -> YBAYROFF'
        
        # Bayer pattern in FITS files seems to be bottom up
        # but AZOTEA use top-bottom, so we need two swap both halves
        if bayer_pattern is None:
            bayer_comment = header.comments['BAYERPAT']
            if not bayer_comment.startswith('Top down convention.'):
                old_bayer_pattern = header['BAYERPAT']
                bayer_pattern = old_bayer_pattern[2:4] + old_bayer_pattern[0:2]
                header['BAYERPAT'] = bayer_pattern
                header.comments['BAYERPAT'] = "Top down convention. (0,0) is upper left"
                header['COLORTYP'] = bayer_pattern
                header.comments['COLORTYP'] = "Top down convention. (0,0) is upper left"
                header['HISTORY'] = f'Flipped existing BAYERPAT & COLORTYP from {old_bayer_pattern} to {bayer_pattern}'
        else:
            old_bayer_pattern = header['BAYERPAT']
            if old_bayer_pattern != bayer_pattern:
                header['BAYERPAT'] = bayer_pattern
                header.comments['BAYERPAT'] = "Top down convention. (0,0) is upper left"
                header['COLORTYP'] = bayer_pattern
                header.comments['COLORTYP'] = "Top down convention. (0,0) is upper left"
                header['HISTORY'] = f'Forced BAYERPAT & COLORTYP from {old_bayer_pattern} to {bayer_pattern}'
        
        if comment is not None:
            header['COMMENT'] = comment

