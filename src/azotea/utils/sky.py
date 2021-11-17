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

#--------------
# local imports
# -------------

from azotea import __version__
from azotea.utils import NAMESPACE, log, chop

from azotea.utils.roi import Point, Rect
from azotea.logger  import startLogging, setLogLevel
from azotea.error import IncorrectTimestampError
from azotea import FITS_HEADER_TYPE, EXIF_HEADER_TYPE
from azotea.gui.widgets.date import DATE_SELECTION_ALL, DATE_SELECTION_DATE_RANGE, DATE_SELECTION_LATEST_NIGHT, DATE_SELECTION_LATEST_MONTH


# ----------------
# Module constants
# ----------------

NAMESPACE = 'CTRL '

# RGGB => R = [x=0,y=0], G1 = [x=1,y=0], G2 = [x=0,y=1], B = [x=1,y=1]
# BGGR => R = [x=1,y=1], G1 = [x=1,y=0], G2 = [x=0,y=1], B = [x=0,y=0]
# GRBG => R = [x=1,y=0], G1 = [x=0,y=0], G2 = [x=1,y=1], B = [x=0,y=1]
# GBRG => R = [x=0,y=1], G1 = [x=0,y=0], G2 = [x=1,y=1], B = [x=1,y=0]

CFA_PATTERNS = {
    # Esto era segun mi entendimiento
    'RGGB' : {'R':{'x': 0,'y': 0}, 'G1':{'x': 1,'y': 0}, 'G2':{'x': 0,'y': 1}, 'B':{'x': 1,'y': 1}}, 
    'BGGR' : {'R':{'x': 1,'y': 1}, 'G1':{'x': 1,'y': 0}, 'G2':{'x': 0,'y': 1}, 'B':{'x': 0,'y': 0}},
    'GRBG' : {'R':{'x': 1,'y': 0}, 'G1':{'x': 0,'y': 0}, 'G2':{'x': 1,'y': 1}, 'B':{'x': 0,'y': 1}},
    'GBRG' : {'R':{'x': 0,'y': 1}, 'G1':{'x': 0,'y': 0}, 'G2':{'x': 1,'y': 1}, 'B':{'x': 1,'y': 0}},
}

CSV_COLUMNS = (
    'session', 
    'observer', 
    'organization', 
    'location', 
    'type', 
    'tstamp', 
    'name', 
    'model', 
    'iso',
    'roi',
    'dark_roi',
    'exptime',
    'aver_signal_R1',
    'std_signal_R1',
    'aver_signal_G2',
    'std_signal_G2',
    'aver_signal_G3',
    'std_signal_G3',
    'aver_signal_B4',
    'std_signal_B4',
    'aver_dark_R1',
    'std_dark_R1',
    'aver_dark_G2',
    'std_dark_G2',
    'aver_dark_G3',
    'std_dark_G3',
    'aver_dark_B4',
    'std_dark_B4',
    'bias',
)

STDDEV_COL_INDEX = (
    CSV_COLUMNS.index('std_signal_R1'),
    CSV_COLUMNS.index('std_signal_G2'),
    CSV_COLUMNS.index('std_signal_G3'),
    CSV_COLUMNS.index('std_signal_B4'),
    CSV_COLUMNS.index('std_dark_R1'),
    CSV_COLUMNS.index('std_dark_G2'),
    CSV_COLUMNS.index('std_dark_G3'),
    CSV_COLUMNS.index('std_dark_B4'),
)

AVER_COL_INDEX = (
    CSV_COLUMNS.index('aver_signal_R1'),
    CSV_COLUMNS.index('aver_signal_G2'),
    CSV_COLUMNS.index('aver_signal_G3'),
    CSV_COLUMNS.index('aver_signal_B4'),
    CSV_COLUMNS.index('aver_dark_R1'),
    CSV_COLUMNS.index('aver_dark_G2'),
    CSV_COLUMNS.index('aver_dark_G3'),
    CSV_COLUMNS.index('aver_dark_B4'),
)

OBSERVER_ORGANIZATION = CSV_COLUMNS.index('organization')
LOCATION = CSV_COLUMNS.index('location')

# -----------------------
# Module global variables
# -----------------------

log = Logger(namespace=NAMESPACE)

# ------------------------
# Module Utility Functions
# ------------------------

def postprocess(item):
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


def region_stats(img, cfa, color, rect):
     x, y = CFA_PATTERNS[cfa][color]['x'], CFA_PATTERNS[cfa][color]['y']
     debayered_plane = img.raw_image[y::2, x::2]
     section = debayered_plane[rect.y1:rect.y2, rect.x1:rect.x2]
     average, variance = round(section.mean(),1), round(section.var(),3)
     return average, variance


def processImage(name, directory, rect, cfa_pattern, row):
     # THIS IS HEAVY STUFF TO BE IMPLEMENTED IN A THREAD
     with rawpy.imread(os.path.join(directory, name)) as img:
        # Debayerize process and calculate stats
        row['aver_signal_R'] , row['vari_signal_R']  = region_stats(img, cfa_pattern, 'R', rect)
        row['aver_signal_G1'], row['vari_signal_G1'] = region_stats(img, cfa_pattern, 'G1', rect)
        row['aver_signal_G2'], row['vari_signal_G2'] = region_stats(img, cfa_pattern, 'G2', rect)
        row['aver_signal_B'] , row['vari_signal_B']  = region_stats(img, cfa_pattern, 'B', rect)
