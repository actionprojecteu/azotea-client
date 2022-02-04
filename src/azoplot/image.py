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
import traceback

# -------------------
# Third party imports
# -------------------

import exifread
import rawpy
from astropy.io import fits

import numpy as np

import matplotlib as mpl
from matplotlib import pyplot as plt

from mpl_toolkits.axes_grid1 import make_axes_locatable
from matplotlib.colors import LogNorm

#--------------
# local imports
# -------------

#--------------
# local imports
# -------------

from azotea              import FITS_HEADER_TYPE, EXIF_HEADER_TYPE
from azotea.utils.image  import scan_non_empty_dirs
from azotea.utils.camera import bayer_from_exif, BAYER_PTN_LIST
from azotea.utils.roi    import Rect, Point
from azotea.utils.sky    import get_debayered_for_channel

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


# Algunos formatos de estilo de los plots
#mpl.rcParams['text.latex.unicode']=True
mpl.rcParams['text.usetex'] = False
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Verdana']
plt.rcParams['font.size'] = 8
plt.rcParams['lines.linewidth'] = 4.
plt.rcParams['axes.labelsize'] = 'small'
plt.rcParams['grid.linewidth'] = 1.0
plt.rcParams['grid.linestyle'] = ':'
plt.rcParams['xtick.minor.size'] = 4
plt.rcParams['xtick.major.size'] = 8
plt.rcParams['ytick.minor.size'] = 4 
plt.rcParams['ytick.major.size'] = 8
plt.rcParams['figure.figsize']   = 18,9
plt.rcParams['figure.subplot.bottom'] = 0.15
plt.rcParams['ytick.labelsize'] = 10
plt.rcParams['xtick.labelsize'] = 10
mpl.rcParams['xtick.direction'] = 'out'

# ----------
# Exceptions
# ----------

class UnknownBayerPatternError(Exception):
    '''Unknown Bayer Pattern'''
    def __str__(self):
        s = self.__doc__
        if self.args:
            s = ' {0}: {1}'.format(s, str(self.args[0]))
        s = '{0}.'.format(s)
        return s

# ------------------------
# Module utility functions
# ------------------------

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

def bayer_fits(header):
    bayer     = header.get('BAYERPAT')
    if bayer is None:
        return None
    swmodify  = header.get('SWMODIFY')
    if swmodify == 'azofits':
        return bayer
    swcreator = header.get('SWCREATE')
    if swcreator == 'SharpCap':
        # Swap halves
        bayer = bayer[2:4] + bayer[0:2]
        return bayer

def metadata_fits(filepath):
    metadata = dict()
    with fits.open(filepath, memmap=False) as hdu_list:
        header = hdu_list[0].header
        metadata['header_type']  = FITS_HEADER_TYPE
        metadata['filepath'] = filepath
        metadata['bayer']    = bayer_fits(header)
        metadata['height']   = header['NAXIS2']
        metadata['width']    = header['NAXIS1']
        metadata['model']    = header.get('INSTRUNE')
        metadata['exptime']  = header.get('EXPTIME')
        metadata['date_obs'] = header.get('DATE_OBS')
        metadata['gain']     = header.get('LOG-GAIN')
        metadata['iso']      = None
        focal_length = header.get('FOCALLEN')
        diameter     = header.get('APTDIA')
        metadata['f_number']  = None  if focal_length is None and diameter is None else round(focal_length/diameter,1)
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
        bayer_pattern = bayer_from_exif(img)
    metadata['height']   = imageHeight
    metadata['width']    = imageWidth
    metadata['bayer']    = bayer_pattern
    return metadata


def get_metadata(filepath, header_type):
    if header_type == FITS_HEADER_TYPE:
        metadata = metadata_fits(filepath)
    else:
        metadata = metadata_exif(filepath)
    return metadata


def centered_roi(metadata, width, height):
    rect = Rect(x1=0, y1=0, x2=width, y2=height)
    imageHeight, imageWidth = metadata['height'], metadata['width']
    imageHeight = imageHeight //2 # From raw dimensions without debayering
    imageWidth =  imageWidth  //2  # to dimensions we actually handle
    width, height = rect.dimensions()
    center=Point(imageWidth//2,imageHeight//2)
    x1 = (imageWidth  -  width)//2
    y1 = (imageHeight - height)//2
    rect += Point(x1,y1)  # Shift ROI using this (x1,y1) point
    result = rect.to_dict()
    return result


def get_pixels_and_plot(filepath, metadata, roi):
    if metadata['header_type'] == FITS_HEADER_TYPE:
        with fits.open(filepath, memmap=False) as hdu_list:
            raw_pixels = hdu_list[0].data
            # This must be executed unther the context manager
            # for raw_pixels to become valid
            plot_4_channels(raw_pixels, roi, metadata)
    else:
         with rawpy.imread(filepath) as img:
            raw_pixels = img.raw_image
            # This must be executed unther the context manager
            # for raw_pixels to become valid
            plot_4_channels(raw_pixels, roi, metadata)
           
    

def stat_display(channel, roi):
    x1, x2, y1, y2 = roi['x1'], roi['x2'], roi['y1'], roi['y2']
    plt.plot((x1,x1),(y1,y2),'k-',lw=1)
    plt.plot((x2,x2),(y1,y2),'k-',lw=1)
    plt.plot((x1,x2),(y1,y1),'k-',lw=1)
    plt.plot((x1,x2),(y2,y2),'k-',lw=1)
    aver = channel[y1:y2,x1:x2].mean()
    std  = channel[y1:y2,x1:x2].std()
    aver_str = '\u03BC = ' + str(round(aver, 1))
    std_str  = '\u03C3 = ' + str(round(std,1))
    plt.text(x1+(x2-x1)/20, (y1+y2)/2-(y2-y1)/5, aver_str, ha='left', va='center')
    plt.text(x1+(x2-x1)/20, (y1+y2)/2+(y2-y1)/5, std_str, ha='left', va='center')
    return aver, std



def plot_4_channels(raw_pixels, roi, metadata, vmin=0, vmax=30000):
    bayer_pattern = metadata['bayer']
    image_R1 = get_debayered_for_channel(raw_pixels, bayer_pattern, 'R')
    image_G2 = get_debayered_for_channel(raw_pixels, bayer_pattern, 'G1')
    image_G3 = get_debayered_for_channel(raw_pixels, bayer_pattern, 'G2')
    image_B4 = get_debayered_for_channel(raw_pixels, bayer_pattern, 'B')

    figura = plt.figure(figsize=(10,6))

    ax1    = figura.add_subplot(221)
    img    = ax1.imshow(image_R1,cmap='Reds',vmin=vmin,vmax=vmax)
    plt.text(0.05, 0.90,'R1', ha='left', va='center', transform=ax1.transAxes, fontsize=10)
    r1_mean_center, r1_std_center = stat_display(image_R1, roi)
    divider = make_axes_locatable(ax1)
    cax1 = divider.append_axes("right", size="5%", pad=0.05)
    figura.colorbar(img, cax=cax1)
    ax1.axes.get_yaxis().set_ticks([])
    ax1.axes.get_xaxis().set_ticks([])

    ax3 = figura.add_subplot(222)
    img = ax3.imshow(image_G2,cmap='Greens',vmin=vmin,vmax=vmax)
    plt.text(0.05, 0.90,'G2', ha='left', va='center', transform=ax3.transAxes, fontsize=10)
    g2_mean_center, g2_std_center = stat_display(image_G2, roi)
    divider = make_axes_locatable(ax3)
    cax3 = divider.append_axes("right", size="5%", pad=0.05)
    figura.colorbar(img, cax=cax3)
    ax3.axes.get_yaxis().set_ticks([])
    ax3.axes.get_xaxis().set_ticks([])

    ax5=figura.add_subplot(223)
    img = ax5.imshow(image_G3,cmap='Greens',vmin=vmin,vmax=vmax)
    plt.text(0.05, 0.90,'G3', ha='left', va='center', transform=ax5.transAxes, fontsize=10)
    g3_mean_center, g3_std_center = stat_display(image_G3, roi)
    divider = make_axes_locatable(ax5)
    cax5 = divider.append_axes("right", size="5%", pad=0.05)
    figura.colorbar(img, cax=cax5)
    ax5.axes.get_yaxis().set_ticks([])
    ax5.axes.get_xaxis().set_ticks([])

    ax7=figura.add_subplot(224)
    img = ax7.imshow(image_B4,cmap='Blues',vmin=vmin,vmax=vmax)
    plt.text(0.05, 0.90,'B4', ha='left', va='center', transform=ax7.transAxes, fontsize=10)
    b4_mean_center, b4_std_center = stat_display(image_B4, roi)
    divider = make_axes_locatable(ax7)
    cax7 = divider.append_axes("right", size="5%", pad=0.05)
    figura.colorbar(img, cax=cax7)
    ax7.axes.get_yaxis().set_ticks([])
    ax7.axes.get_xaxis().set_ticks([])

 
    basename    = os.path.basename(metadata.get('filepath'))
    header_type = metadata.get('header_type')
    gain        = metadata.get('gain')
    iso         = metadata.get('iso')
    model       = metadata.get('model')
    exptime     = metadata.get('exptime')
    date_obs    = metadata.get('date_obs')

    if header_type == 'FITS_HEADER_TYPE':
        label =f"{model}   gain = {gain}  exposure = {exptime} s."
    else:
        label =f"{model}   iso = {iso}  exposure = {exptime} s."

    plt.text(-0.0, 1.05, basename, ha='left', va='center', transform=ax7.transAxes, fontsize=10)
    plt.text(0.4, 1.12,  date_obs, ha='left', va='center', transform=ax7.transAxes, fontsize=10)    
    plt.text(0.4, 1.05,  label,    ha='left', va='center', transform=ax7.transAxes, fontsize=10)
   
    plt.tight_layout()
    plt.show()



# ===================
# Module entry points
# ===================

def do_single(filepath, options, i=1, N=1):
    log.info(f"prcessing {filepath}")
    header_type = find_header_type(filepath)
    metadata = get_metadata(filepath, header_type)
    roi = centered_roi(metadata, options.width, options.height)
    metadata['bayer'] = options.bayer if options.bayer else metadata['bayer']
    if not metadata['bayer']:
        raise UnknownBayerPatternError(f"Choose among {BAYER_PTN_LIST}")
    get_pixels_and_plot(filepath, metadata, roi)


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
                    traceback.print_exc()
                    #continue
                except Exception as e:
                    raise e
