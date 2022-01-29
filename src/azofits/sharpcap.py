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

#--------------
# local imports
# -------------

from astropy.io import fits

# ----------------
# Module constants
# ----------------

GAIN_REGEXP = re.compile(r'Gain=(\d+)')

# -----------------------
# Module global variables
# -----------------------

log = logging.getLogger("azofits")

# Ex ception

class MissinGainError(Exception):
    '''SharpCap din not provide any gain value in metadata'''
    def __str__(self):
        s = self.__doc__
        if self.args:
            s = ' {0}: {1}'.format(s, str(self.args[0]))
        s = '{0}.'.format(s)
        return s

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
    raise MissinGainError(basename)

# --------------------
# Module main function
# --------------------

def fits_edit(filepath, swcreator, swcomment, model, image_type, bayer_pattern, gain, x_pixsize, y_pixsize):
    basename = os.path.basename(filepath)
    now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')
    if gain is None:
        gain = _fits_read_gain(filepath)

    with fits.open(filepath, mode='update') as hdul:
        header = hdul[0].header

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
       
        # Handling of excessive seconds decimals in DATE-OBS
        tstamp = header['DATE-OBS']
        if len(tstamp) > 26:
            tstamp = tstamp[0:26]
            header['DATE-OBS'] = tstamp
            header['HISTORY'] = 'Fixed excessive decimals (>6) in DATE-OBS'
        
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
        
        # Handling of LOG-GAIN
        old_gain = header.get('LOG-GAIN')
        if old_gain is None: 
            header['LOG-GAIN'] = gain
            header.comments['LOG-GAIN'] = 'Logarithmic gain in 0.1 dB units'
            header['HISTORY'] = 'Added LOG-GAIN'

        # Handling of SWMODIFY
        swmodify = header.get('SWMODIFY')
        if swmodify is None:
            header['SWMODIFY'] = 'azofits'
            header.comments['SWMODIFY'] = 'Updated on ' + now
            header['HISTORY'] = 'Added SWMODIFY'