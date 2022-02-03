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
import glob
import logging

# -------------------
# Third party imports
# -------------------

import exifread
import rawpy
from astropy.io import fits 

#--------------
# local imports
# -------------

#--------------
# local imports
# -------------

from azotea              import FITS_HEADER_TYPE, EXIF_HEADER_TYPE
from azotea.utils.image  import scan_non_empty_dirs
from azotea.utils.roi    import Rect, Point
from azotea.utils.sky    import processImage

from azotea.utils.camera import camera_from_image

# ----------------
# Module constants
# ----------------

FITS_LOWER_EXTENSIONS = ('*.fit',  '*.fits', '*.fts')
EXIF_LOWER_EXTENSIONS = ('*.cr2', '*.nef', '*.orf', '*.pef')
FITS_EXTENSIONS       = FITS_LOWER_EXTENSIONS + tuple(s.upper() for s in FITS_LOWER_EXTENSIONS)
EXIF_EXTENSIONS       = EXIF_LOWER_EXTENSIONS + tuple(s.upper() for s in EXIF_LOWER_EXTENSIONS)

EXTENSIONS = EXIF_EXTENSIONS + FITS_EXTENSIONS


# -----------------------
# Module global variables
# -----------------------

log = logging.getLogger('azoplot')

# ------------------------
# Module utility functions
# ------------------------

def raw_dimensions_fits(filepath):
    with fits.open(filepath, memmap=False) as hdu_list:
        header = hdu_list[0].header
    return header['NAXIS2'], header['NAXIS1']
  
     
def raw_dimensions_exif(filepath):
    # This is to properly detect and EXIF image
    with open(filepath, 'rb') as f:
        exif = exifread.process_file(f, details=False)
        if not exif:
            raise ValueError("Could not open EXIF metadata")
    # Get the real RAW dimensions instead
    with rawpy.imread(filepath) as img:
        imageHeight, imageWidth = img.raw_image.shape
    return  imageHeight, imageWidth


def toDateTime(tstamp):
    for fmt in ('%Y:%m:%d %H:%M:%S','%Y-%m-%dT%H:%M:%S.%f', '%Y-%m-%dT%H:%M:%S'):
        try:
            tstamp_obj = datetime.datetime.strptime(tstamp, fmt)
        except ValueError as e:
            continue
        else:
            break
    if not tstamp_obj:
        raise IncorrectTimestampError(tstamp)
    else:
        return tstamp_obj.strftime('%Y-%m-%dT%H:%M:%S')


def metadata_fits(filepath):
    metadata = dict()
    with fits.open(filepath, memmap=False) as hdu_list:
        header = hdu_list[0].header
        metadata['header_type']  = FITS_HEADER_TYPE
        metadata['filepath'] = filepath
        metadata['height']   = header['NAXIS2']
        metadata['width']    = header['NAXIS1']
        metadata['model']    = header.get('INSTRUNE', 'Unknown')
        metadata['exptime']  = header.get('EXPTIME',  'Unknown')
        metadata['date_obs'] = header.get('DATE_OBS', 'Unknown')
        metadata['gain']     = header.get('LOG-GAIN', 'Unknown')
        metadata['iso']      = None
        focal_length = header.get('FOCALLEN')
        diameter     = header.get('APTDIA')
        metadata['focal_length'] = 'Unknown' if focal_length is None else focal_length
        metadata['f_number']     ='Unknown'  if focal_length is None and diameter is None else round(focal_length/diameter,1)
    return metadata


def metadata_exif(filepath):
    metadata = dict()
    with open(filepath, 'rb') as f:
        exif = exifread.process_file(f, details=False)
        if not exif:
            message = 'Could not open EXIF metadata'
            raise ValueError(message)
        metadata['header_type']  = EXIF_HEADER_TYPE
        metadata['filepath']     = filepath
        metadata['model']        = str(exif.get('Image Model', None)).strip()
        metadata['iso']          = str(exif.get('EXIF ISOSpeedRatings', None))
        metadata['focal_length'] = float(Fraction(str(exif.get('EXIF FocalLength', 0))))
        metadata['f_number']     = float(Fraction(str(exif.get('EXIF FNumber', 0))))
        metadata['exptime']      = float(Fraction(str(exif.get('EXIF ExposureTime', 0))))
        metadata['date_id'], row['time_id'], row['widget_date'], row['widget_time'] = toDateTime(str(exif.get('Image DateTime', None)))
        # Fixes missing Focal Length and F/ ratio
        metadata['focal_length'] = 'Unknown' if row['focal_length'] == 0 else metadata['focal_length']
        metadata['f_number']     = 'Unknown' if row['f_number']     == 0 else metadata['f_number']
        # Fixed GAIN for EXIF DSLRs that provide ISO sensivity
        metadata['gain'] = None
    # Get the real RAW dimensions instead
    with rawpy.imread(filepath) as img:
        imageHeight, imageWidth = img.raw_image.shape
    metadata['height']   = imageHeight
    metadata['width']    = imageWidth
    return metadata


def centered_roi(filepath, header_type, width, height):
    rect = Rect(x1=0, y1=0, x2=width, y2=height)
    extension = os.path.splitext(filepath)[1]
    if header_type == FITS_HEADER_TYPE:
        imageHeight, imageWidth = raw_dimensions_fits(filepath)
    else:
        imageHeight, imageWidth = raw_dimensions_exif(filepath)
    imageHeight = imageHeight //2 # From raw dimensions without debayering
    imageWidth =  imageWidth  //2  # to dimensions we actually handle
    width, height = rect.dimensions()
    center=Point(imageWidth//2,imageHeight//2)
    x1 = (imageWidth  -  width)//2
    y1 = (imageHeight - height)//2
    rect += Point(x1,y1)  # Shift ROI using this (x1,y1) point
    result = rect.to_dict()
    return result

     
def find_header_type(filepath):
    extension = '*' + os.path.splitext(filepath)[1]
    if extension in FITS_EXTENSIONS:
        result = FITS_HEADER_TYPE
    elif extension in EXIF_EXTENSIONS:
        result = EXIF_HEADER_TYPE
    else:
        result = None
        log.error("NO EXTENSION DETECTED")
    return result


def do_single(filepath, options, i=1, N=1):
    log.info(f"prcessing {filepath}")
    #camera = camera_from_image(filepath)
    #print(camera)
    header_type = find_header_type(filepath)
    roi = centered_roi(filepath, header_type, options.width, options.height)
    stats = processImage(
        name          = os.path.basename(filepath), 
        directory     = os.path.dirname(filepath), 
        roi          = roi, 
        header_type   = find_header_type(filepath), 
        bayer_pattern = options.bayer_pattern, 
        row           = {}
    )
    print(stats)


# ===================
# Module entry points
# ===================

def stats(options):
    
    if options.image_file:
        do_single(options.image_file, options)
    else:
        directories = scan_non_empty_dirs(options.images_dir, depth=0)
        directories = set(directories) # get reid of duplicates (a bug in scan_non_empty dir?)
        for directory in directories:
            paths_set = set()
            for extension in EXTENSIONS:
                alist  = glob.glob(os.path.join(directory, extension))
                paths_set  = paths_set.union(alist)
            N = len(paths_set)
            if N:
                log.warning(f"Scanning directory '{directory}'. Found {N} images matching '{EXTENSIONS}'")
            for i, filepath in enumerate(sorted(paths_set), start=1):
                try:
                    do_single(filepath, options, i, N)
                except (FileNotFoundError,) as e:
                    log.critical("[%s] Fatal error => %s", __name__, str(e) )
                    continue
                except Exception as e:
                    raise e
