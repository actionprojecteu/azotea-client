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
from azotea.utils import chop
from azotea.utils.roi import Point, Rect
from azotea.utils.sky import CSV_COLUMNS, postprocess, widget_datetime, processImage
from azotea.logger  import startLogging, setLogLevel
from azotea.error import IncorrectTimestampError
from azotea import FITS_HEADER_TYPE, EXIF_HEADER_TYPE
from azotea.gui.widgets.date import DATE_SELECTION_ALL, DATE_SELECTION_DATE_RANGE, DATE_SELECTION_LATEST_NIGHT, DATE_SELECTION_LATEST_MONTH

# ----------------
# Module constants
# ----------------

NAMESPACE = 'CTRL '

# -----------------------
# Module global variables
# -----------------------

# Support for internationalization
_ = gettext.gettext

log = Logger(namespace=NAMESPACE)

# ------------------------
# Module Utility Functions
# ------------------------



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
        pub.subscribe(self.onStatisticsReq,  'sky_brightness_stats_req')
        pub.subscribe(self.onDeleteReq, 'sky_brightness_delete_req')
        pub.subscribe(self.onAbortReq,  'sky_brightness_abort_stats_req')
        pub.subscribe(self.onExportReq, 'sky_brightness_csv_req')

    def onAbortReq(self):
        self._abort = True
 
    # -----------------------
    # Subscriptions from View
    # ----------------------

    @inlineCallbacks
    def onStatisticsReq(self):
        self._abort = False
        result = yield self.doCheckDefaults()
        if result:
            yield self.doStatistics()


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
        return(result)


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
        return(result)



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
    def doStatistics(self):
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
                return(None)
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


    

    
           