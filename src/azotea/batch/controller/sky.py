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

import os.path
import csv

# ---------------
# Twisted imports
# ---------------

from twisted.logger   import Logger
from twisted.internet.defer import inlineCallbacks
from twisted.internet.threads import deferToThread

# -------------------
# Third party imports
# -------------------

from pubsub import pub

#--------------
# local imports
# -------------

from azotea.logger  import setLogLevel
from azotea.utils.roi import Rect
from azotea.utils.sky import CSV_COLUMNS, postprocess, widget_datetime, processImage
from azotea import FITS_HEADER_TYPE, EXIF_HEADER_TYPE
from azotea import DATE_SELECTION_ALL, DATE_SELECTION_DATE_RANGE, DATE_SELECTION_LATEST_NIGHT, DATE_SELECTION_LATEST_MONTH
from azotea.batch.controller import NAMESPACE, log

# ----------------
# Module constants
# ----------------

# -----------------------
# Module global variables
# -----------------------

# ------------------------
# Module Utility Functions
# ------------------------

# --------------
# Module Classes
# --------------

class SkyBackgroundController:

    NAME = NAMESPACE
    
    def __init__(self, config, model):
        self.model  = model
        self.sky    = model.sky
        self.image  = model.image
        self.roi    = model.roi
        self.config = config
        self.observerCtrl = None
        self.roiCtrl      = None
        self.publish = False
        setLogLevel(namespace=NAMESPACE, levelStr='info')
        pub.subscribe(self.onStatisticsReq,  'sky_brightness_stats_req')   

    # --------------
    # Event handlers
    # --------------

    @inlineCallbacks
    def onStatisticsReq(self):
        try:
            result = yield self.doCheckDefaults()
            if result:
                yield self.doStatistics()
            else:
                pub.sendMessage('file_quit', exit_code = 1)
        except Exception as e:
            log.failure('{e}',e=e)
            pub.sendMessage('file_quit', exit_code = 1)
        else:
            if self.publish:
                pub.sendMessage("publishing_publish_req")
            else:
                pub.sendMessage('file_quit')

    # --------------
    # Helper methods
    # --------------

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
            log.error("Sky Background Processor: {m}", m=message)
            result = False
        return(result)


    @inlineCallbacks
    def doStatistics(self):
        # Default settings extracted by doCheckDefaults()
        conditions = {
            'roi_id'     : self.roi_id,
        }

        roi_dict = yield self.roi.loadById(conditions)
        rect = Rect.from_dict(roi_dict)
        image_id_list = yield self.sky.pending(conditions)
        N_stats = len(image_id_list)
        for i, (image_id,) in enumerate(image_id_list):
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
                log.error("Sky Background Processor: {name} [{p}%]", name=row['name'], p=(100*i//N_stats))
                return(None)
            else:
                log.info("Sky Background Processor: {name} [{p}%]", name=row['name'], p=(100*i//N_stats))
                yield self.sky.save(row)
        if N_stats:
            log.info("Sky Background Processor: {n}/{d} images processed", n=i+1, d=N_stats)
        else:
            log.info("Sky Background Processor: No images to process")
        