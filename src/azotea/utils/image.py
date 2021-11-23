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
import hashlib
from fractions import Fraction

# ---------------------
# Third party libraries
# ---------------------

import exifread

#--------------
# local imports
# -------------

from azotea.error import IncorrectTimestampError
from azotea.utils import NAMESPACE, log

# ----------------
# Module constants
# ----------------

# -----------------------
# Module global variables
# -----------------------

# -----------------------
# Module global variables
# -----------------------

# ------------------------
# Module Utility Functions
# ------------------------

def hashfunc(filepath):
    '''Compute a hash from the image'''
    BLOCK_SIZE = 1048576 # 1MByte, the size of each read from the file
    # md5() was the fastest algorithm I've tried
    # but I'm using blake2b with twice the digest size for compatibility
    # with the old AZOTEA software    
    #file_hash = hashlib.md5()
    file_hash = hashlib.blake2b(digest_size=32)
    with open(filepath, 'rb') as f:
        block = f.read(BLOCK_SIZE) 
        while len(block) > 0:
            file_hash.update(block)
            block = f.read(BLOCK_SIZE)
    return file_hash.digest()


def exif_metadata(filename, row):
    with open(filename, 'rb') as f:
        exif = exifread.process_file(f, details=False)
    if not exif:
        log.warn('Could not open EXIF metadata from {file}',file=filename)
        return row
    row['model']        = str(exif.get('Image Model', None)).strip()
    row['iso']          = str(exif.get('EXIF ISOSpeedRatings', None))
    row['focal_length'] = float(Fraction(str(exif.get('EXIF FocalLength', 0))))
    row['f_number']     = float(Fraction(str(exif.get('EXIF FNumber', 0))))
    row['exptime']      = float(Fraction(str(exif.get('EXIF ExposureTime', 0))))
    row['date_id'], row['time_id'], row['widget_date'], row['widget_time'] = toDateTime(str(exif.get('Image DateTime', None)))
   
    # Fixes missing Focal Length and F/ ratio
    row['focal_length'] = row['def_fl'] if row['focal_length'] == 0 else row['focal_length']
    row['f_number']     = row['def_fn'] if row['f_number']     == 0 else row['f_number']

    # Fixed GAIN for EXIF DSLRs that provide ISO sensivity
    row['gain'] = None
    return row


def toDateTime(tstamp):
    tstamp_obj = None
    for fmt in ['%Y:%m:%d %H:%M:%S',]:
        try:
            tstamp_obj = datetime.datetime.strptime(tstamp, fmt)
        except ValueError:
            continue
        else:
            break
    if not tstamp_obj:
        raise IncorrectTimestampError(tstamp)
    else:
        date_id = int(tstamp_obj.strftime('%Y%m%d'))
        time_id = int(tstamp_obj.strftime('%H%M%S'))
        widged_date = tstamp_obj.strftime('%Y-%m-%d')
        widget_time = tstamp_obj.strftime('%H:%M:%S')
        return date_id, time_id, widged_date, widget_time


def hash_and_exif_metadata(filepath, row):
    log.debug('Computing {row.name} MD5 hash', row=row)
    row['hash'] = hashfunc(filepath)
    log.debug('Loading {row.name} EXIF metadata', row=row)
    row = exif_metadata(filepath, row)
