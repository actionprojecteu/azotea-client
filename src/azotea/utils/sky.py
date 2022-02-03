# -*- coding: utf-8 -*-
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
import sys
import csv
import math
import glob
import hashlib
import gettext
import datetime

from fractions import Fraction
from sqlite3 import IntegrityError

# ---------------
# Twisted imports
# ---------------

from twisted.logger   import Logger
from twisted.internet import  reactor, defer
from twisted.internet.defer import inlineCallbacks
from twisted.internet.threads import deferToThread

# -------------------
# Third party imports
# -------------------

from pubsub import pub
import numpy as np
import exifread
import rawpy
from astropy.io import fits

#--------------
# local imports
# -------------

from azotea import __version__
from azotea.utils import chop

from azotea.utils.roi import Point, Rect
from azotea.logger  import startLogging, setLogLevel

from azotea import FITS_HEADER_TYPE, EXIF_HEADER_TYPE
from azotea import DATE_SELECTION_ALL, DATE_SELECTION_DATE_RANGE, DATE_SELECTION_LATEST_NIGHT, DATE_SELECTION_LATEST_MONTH


# ----------------
# Module constants
# ----------------

RAWPY_EXCEPTIONS = (rawpy._rawpy.LibRawIOError, rawpy._rawpy.LibRawFileUnsupportedError)

# RGGB => R = [x=0,y=0], G1 = [x=1,y=0], G2 = [x=0,y=1], B = [x=1,y=1]
# BGGR => R = [x=1,y=1], G1 = [x=1,y=0], G2 = [x=0,y=1], B = [x=0,y=0]
# GRBG => R = [x=1,y=0], G1 = [x=0,y=0], G2 = [x=1,y=1], B = [x=0,y=1]
# GBRG => R = [x=0,y=1], G1 = [x=0,y=0], G2 = [x=1,y=1], B = [x=1,y=0]

CFA_OFFSETS = {
    # Esto era segun mi entendimiento
    'RGGB' : {'R':{'x': 0,'y': 0}, 'G1':{'x': 1,'y': 0}, 'G2':{'x': 0,'y': 1}, 'B':{'x': 1,'y': 1}}, 
    'BGGR' : {'R':{'x': 1,'y': 1}, 'G1':{'x': 1,'y': 0}, 'G2':{'x': 0,'y': 1}, 'B':{'x': 0,'y': 0}},
    'GRBG' : {'R':{'x': 1,'y': 0}, 'G1':{'x': 0,'y': 0}, 'G2':{'x': 1,'y': 1}, 'B':{'x': 0,'y': 1}},
    'GBRG' : {'R':{'x': 0,'y': 1}, 'G1':{'x': 0,'y': 0}, 'G2':{'x': 1,'y': 1}, 'B':{'x': 1,'y': 0}},
}

CSV_COLUMNS = (
    'csv_version',
    'session', 
    'observer', 
    'affiliation', 
    'location', 
    'type', 
    'tstamp', 
    'name', 
    'model', 
    'iso',
    'roi',
    'exptime',
    'aver_signal_R1',
    'std_signal_R1',
    'aver_signal_G2',
    'std_signal_G2',
    'aver_signal_G3',
    'std_signal_G3',
    'aver_signal_B4',
    'std_signal_B4',
    'bias',
)

STDDEV_COL_INDEX = (
    CSV_COLUMNS.index('std_signal_R1'),
    CSV_COLUMNS.index('std_signal_G2'),
    CSV_COLUMNS.index('std_signal_G3'),
    CSV_COLUMNS.index('std_signal_B4'),
)

AVER_COL_INDEX = (
    CSV_COLUMNS.index('aver_signal_R1'),
    CSV_COLUMNS.index('aver_signal_G2'),
    CSV_COLUMNS.index('aver_signal_G3'),
    CSV_COLUMNS.index('aver_signal_B4'),
)

OBSERVER_ORGANIZATION = CSV_COLUMNS.index('affiliation')
LOCATION = CSV_COLUMNS.index('location')

# -----------------------
# Module global variables
# -----------------------

log = Logger(namespace='skybg')

# ------------------------
# Module Utility Functions
# ------------------------

def csv_postprocess(item):
    '''From Variance to StdDev in several columns'''
    index, value = item
    if index == LOCATION:
        kk = chop(value,' - ')
        value = kk[0] if kk[0] == kk[1] else value

    # Calculate stddev from variance and round to one decimal place
    if  index in  STDDEV_COL_INDEX:
        value = round(math.sqrt(value),1)
    # Round the aver_signal channels too
    elif index in AVER_COL_INDEX:
        value = round(value, 3)
    return value


def widget_datetime(date_id, time_id):
    string = f"{date_id:08d}{time_id:06d}"
    dt = datetime.datetime.strptime(string, "%Y%m%d%H%M%S")
    return dt.strftime("%Y-%m-%d"), dt.strftime("%H:%M:%S")


def get_bayer_offsets(bayer_pattern, channel):
     return CFA_OFFSETS[bayer_pattern][channel]['x'], CFA_OFFSETS[bayer_pattern][channel]['y']

def get_debayered_for_channel(raw_pixels, bayer_pattern, channel):
    x, y = get_bayer_offsets(bayer_pattern, channel)
    return raw_pixels[y::2, x::2]

def get_image_roi(debayered_channel, roi):
     y1 = roi['y1'] ; y2 = roi['y2']
     x1 = roi['x1'] ; x2 = roi['x2']
     return debayered_channel[y1:y2, x1:x2]

def region_stats(raw_pixels, bayer_pattern, channel, roi):
     debayered_channel = get_debayered_for_channel(raw_pixels, bayer_pattern, channel)
     section           = get_image_roi(debayered_channel, roi)
     average, variance = round(section.mean(),1), round(section.var(),3)
     return average, variance

def all_channels_stats(raw_pixels, bayer_pattern, roi, row):
    row['aver_signal_R'] , row['vari_signal_R']  = region_stats(raw_pixels, bayer_pattern, 'R', roi)
    row['aver_signal_G1'], row['vari_signal_G1'] = region_stats(raw_pixels, bayer_pattern, 'G1', roi)
    row['aver_signal_G2'], row['vari_signal_G2'] = region_stats(raw_pixels, bayer_pattern, 'G2', roi)
    row['aver_signal_B'] , row['vari_signal_B']  = region_stats(raw_pixels, bayer_pattern, 'B', roi)
    return row

# --------------------
# MAIN DRIVER FUNCTION
# --------------------

def processImage(name, directory, roi, header_type, bayer_pattern, row):
    # THIS IS HEAVY STUFF TO BE IMPLEMENTED IN A THREAD
    filepath = os.path.join(directory, name)
    if header_type == FITS_HEADER_TYPE:
        with fits.open(filepath, memmap=False) as hdu_list:
            raw_pixels = hdu_list[0].data
            # This must be executed unther the context manager
            # for raw_pixels to become valid
            row = all_channels_stats(raw_pixels, bayer_pattern, roi, row)
    else:
         with rawpy.imread(filepath) as img:
            raw_pixels = img.raw_image
            # This must be executed unther the context manager
            # for raw_pixels to become valid
            row = all_channels_stats(raw_pixels, bayer_pattern, roi, row)
    return row

