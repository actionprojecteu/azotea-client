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
from twisted.internet.defer import inlineCallbacks, returnValue
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

from tkazotea import __version__
from tkazotea.utils import Point, Rect, chop
from tkazotea.logger  import startLogging, setLogLevel
from tkazotea.error import IncorrectTimestampError
from tkazotea.gui import FITS_HEADER_TYPE, EXIF_HEADER_TYPE
from tkazotea.gui.widgets.date import DATE_SELECTION_ALL, DATE_SELECTION_DATE_RANGE, DATE_SELECTION_LATEST_NIGHT, DATE_SELECTION_LATEST_MONTH

# ----------------
# Module constants
# ----------------

NAMESPACE = 'CTRL '
DEF_TSTAMP = '%Y-%m-%dT%H:%M:%S'

PUBLISH_PAGE_SIZE = 500

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


# -----------------------
# Module global variables
# -----------------------

# Support for internationalization
_ = gettext.gettext

log = Logger(namespace=NAMESPACE)

# ------------------------
# Module Utility Functions
# ------------------------

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

# --------------
# Module Classes
# --------------

class SkyBackgroundController:

    NAME = NAMESPACE
    
    def __init__(self, parent, view, model):
        self.parent = parent
        self.model = model
        self.view = view
        self.sky    = model.sky
        self.image  = model.image
        self.roi    = model.roi 
        self.config = model.config
        self.observerCtrl = None
        self.roiCtrl      = None
        setLogLevel(namespace=NAMESPACE, levelStr='info')
        self.start()
        self._abort = False
           
    def start(self):
        log.info('starting Sky Background Controller')
        pub.subscribe(self.onStatsReq,  'sky_brightness_stats_req')
        pub.subscribe(self.onDeleteReq, 'sky_brightness_delete_req')
        pub.subscribe(self.onAbortReq,  'sky_brightness_abort_stats_req')
        pub.subscribe(self.onExportReq, 'sky_brightness_csv_req')

    def onAbortReq(self):
        self._abort = True
 
    # -----------------------
    # Subscriptions from View
    # ----------------------

    @inlineCallbacks
    def onStatsReq(self):
        self._abort = False
        result = yield self.doCheckDefaults()
        if result:
            yield self.doStats()


    @inlineCallbacks
    def onDeleteReq(self, date):
        observer_id, tmp = yield self.observerCtrl.getDefault()
        filter_dict = {'observer_id': observer_id}
        date_selection = date['date_selection']
        if date_selection == DATE_SELECTION_ALL:
            count = yield self.sky.countAll(filter_dict)
            message = _("Deleting {0} images").format(count)
            accepted = self.view.messageBoxAcceptCancel(message=message, who= _("Sky Backround Processor"))
            if accepted:
                yield self.sky.deleteAll(filter_dict)
        elif date_selection == DATE_SELECTION_LATEST_NIGHT:
            count = yield self.sky.getLatestNightCount(filter_dict)
            message = _("Deleting {0} images").format(count)
            accepted = self.view.messageBoxAcceptCancel(message=message, who= _("Sky Backround Processor"))
            if accepted:
                yield self.sky.deleteLatestNight(filter_dict)
        elif date_selection == DATE_SELECTION_LATEST_MONTH:
            count = yield self.sky.getLatestMonthCount(filter_dict)
            message = _("Deleting {0} images").format(count)
            accepted = self.view.messageBoxAcceptCancel(message=message, who= _("Sky Backround Processor"))
            if accepted:
                yield self.sky.deleteLatestMonth(filter_dict)
        elif date_selection == DATE_SELECTION_DATE_RANGE:
            filter_dict['start_date_id'] = int(date['start_date'])
            filter_dict['end_date_id']   = int(date['end_date'])
            count = yield self.sky.getDateRangeCount(filter_dict)
            message = _("Deleting {0} images").format(count)
            accepted = self.view.messageBoxAcceptCancel(message=message, who= _("Sky Backround Processor"))
            if accepted:
                yield self.sky.deleteDateRange(filter_dict)
        else:
            pass


    @inlineCallbacks
    def onExportReq(self, date):
        self._abort = False
        result = yield self.doCheckDefaultsExport()
        if result:
            yield self.doExport(date)


    @inlineCallbacks
    def doCheckDefaults(self):
        result = True
        errors = list()
        log.debug('doCheckDefaults()')
        default_roi_id, tmp = yield self.roiCtrl.getDefault()
        if default_roi_id:
            self.roi_id = int(default_roi_id)
        else:
            self.roi_id = None
            errors.append( _("- No default ROI selected.") )
        if errors:
            error_list = '\n'.join(errors)
            message = _("These things are missing:\n{0}").format(error_list)
            self.view.messageBoxError(who=_("Sky Background Processor"),message=message)
            result = False
        returnValue(result)


    @inlineCallbacks
    def doCheckDefaultsExport(self):
        result = True
        errors = list()
        default_roi_id, tmp = yield self.roiCtrl.getDefault()
        if default_roi_id:
            self.roi_id = int(default_roi_id)
        else:
            self.roi_id = None
            errors.append( _("- No default ROI selected.") )
        default_observer_id, default_observer_details = yield self.observerCtrl.getDefault()
        if default_observer_id:
            self.observer_id = int(default_observer_id)
            self.observer_name = default_observer_details['surname'].replace(' ', '_')
        else:
            self.observer_id = None
            errors.append( _("- No default observer selected.") )
        if errors:
            error_list = '\n'.join(errors)
            message = _("These things are missing:\n{0}").format(error_list)
            self.view.messageBoxError(who=_("Sky Background Processor"),message=message)
            result = False
        returnValue(result)



    @inlineCallbacks
    def doExport(self, date):
        filter_dict = {'observer_id': self.observer_id}
        date_selection = date['date_selection']
        if date_selection == DATE_SELECTION_ALL:
            filename = f'{self.observer_name}-all.csv'
            contents = yield self.sky.exportAll(filter_dict)
        elif date_selection == DATE_SELECTION_LATEST_NIGHT:
            year, month, day = yield self.sky.getLatestNight(filter_dict)
            filename = f'{self.observer_name}-{year}{month}{day:02d}.csv'
            contents = yield self.sky.exportLatestNight(filter_dict)
        elif date_selection == DATE_SELECTION_LATEST_MONTH:
            year, month, day = yield self.sky.getLatestMonth(filter_dict)
            filename = f'{self.observer_name}-{year}{month}{day:02d}.csv'
            contents = yield self.sky.exportLatestMonth(filter_dict)
        elif date_selection == DATE_SELECTION_DATE_RANGE:
            filter_dict['start_date_id'] = int(date['start_date'])
            filter_dict['end_date_id']   = int(date['end_date'])
            filename = f"{self.observer_name}-{date['start_date']}-{date['end_date']}.csv"
            contents = yield self.sky.exportDateRange(filter_dict)
        else:
            log.error("ESTO NO DEBERIA DARSE")
        path = self.view.saveFileDialog(
            title     = _("Export CSV File"),
            extension = '.csv',
            filename  = filename
        ) 
        with open(path,'w') as fd:
            writer = csv.writer(fd, delimiter=';')
            writer.writerow(CSV_COLUMNS)
            for row in contents:
                row = map(postprocess, enumerate(row))
                writer.writerow(row)
        log.info("Export complete to {path}",path=path)



    @inlineCallbacks
    def doStats(self):
        # Default settings extracted by doCheckDefaults()
        conditions = {
            'roi_id'     : self.roi_id,
        }
        roi_dict = yield self.roi.loadById({'roi_id': self.roi_id})
        log.info("ROI DICT = {r}",r=roi_dict)
        rect = Rect.from_dict(roi_dict)
        image_id_list = yield self.sky.pending(conditions)
        N_stats = len(image_id_list)
        for i, (image_id,) in enumerate(image_id_list):
            if self._abort:
                break
            name, directory, exptime, cfa_pattern, camera_id, date_id, time_id, observer_id, location_id = yield self.image.getInitialMetadata({'image_id':image_id})
            w_date, w_time = widget_datetime(date_id, time_id) 
            row = {
                'name'       : name,
                'image_id'   : image_id,
                'observer_id': observer_id,
                'location_id': location_id,
                'roi_id'     : self.roi_id,
                'camera_id'  : camera_id,
                'date_id'    : date_id,
                'time_id'    : time_id,
                'widget_date': w_date,  # for display purposes only
                'widget_time': w_time,  # for display purposes only
                'exptime'    : exptime, # for display purposes only
            }
            try:
                yield deferToThread(processImage, name, directory, rect, cfa_pattern, row)
            except Exception as e:
                log.failure('{e}', e=e)
                self.view.statusBar.update( _("SKY BACKGROUND"), row['name'], (100*i//N_stats), error=True)
                returnValue(None)
            else:
                self.view.statusBar.update( _("SKY BACKGROUND"), row['name'], (100*i//N_stats), error=False)
                yield self.sky.save(row)
                self.view.mainArea.displaySkyMeasurement(row['name'],row)
        if N_stats:
            message = _("Sky background: {0}/{1} images computed").format(i+1,N_stats)
            self.view.messageBoxInfo(who=_("Sky backround statistics"),message=message)
        else:
            message = _("No images to process")
            self.view.messageBoxWarn(who=_("Sky backround statistics"),message=message)
        self.view.statusBar.clear()


    

    
           