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
import hashlib
from fractions import Fraction

# ---------------------
# Third party libraries
# ---------------------

import exifread

#--------------
# local imports
# -------------

# ----------------
# Module constants
# ----------------

# -----------------------
# Module global variables
# -----------------------

# -----------------------
# Module global variables
# -----------------------

# ----------
# Exceptions
# ----------

class IncorrectTimestampError(ValueError):
    '''Could not parse such timestamp'''
    def __str__(self):
        s = self.__doc__
        if self.args:
            s = ' {0}: {1}'.format(s, str(self.args[0]))
        s = '{0}.'.format(s)
        return s


# ------------------------
# Module Utility Functions
# ------------------------

def scan_non_empty_dirs(root, depth=None):
    if os.path.basename(root) == '':
        root = root[:-1]
    dirs = [dirpath for dirpath, dirs, files in os.walk(root) if files]
    dirs.append(root)   # Add it for images just under the root folder
    if depth is None:
        return dirs 
    L = len(root.split(sep=os.sep))
    return list(filter(lambda d: len(d.split(sep=os.sep)) - L <= depth, dirs))


def hash_func(filepath):
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
        message = 'Could not open EXIF metadata'
        raise ValueError(message)
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
    row['hash'] = hash_func(filepath)
    row = exif_metadata(filepath, row)
