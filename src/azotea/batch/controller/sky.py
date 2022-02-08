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
from azotea.utils.sky import processImage, RAWPY_EXCEPTIONS

# ----------------
# Module constants
# ----------------

NAMESPACE = 'skybg'
BUFFER_SIZE = 50   # Cache size before doing database writes.
PAGE_SIZE   = 2*BUFFER_SIZE # Display progress every N images

# -----------------------
# Module global variables
# -----------------------

log = Logger(namespace=NAMESPACE)

# ------------------------
# Module Utility Functions
# ------------------------

# --------------
# Module Classes
# --------------

class SkyBackgroundController:

    NAME = NAMESPACE
    
    def __init__(self, config, model, next_event):
        self.model  = model
        self.sky    = model.sky
        self.image  = model.image
        self.roi    = model.roi
        self.config = config
        self.next_event = next_event
        self.observerCtrl = None
        self.roiCtrl      = None
        setLogLevel(namespace=NAMESPACE, levelStr='info')
        pub.subscribe(self.onStatisticsReq,  'sky_brightness_stats_req')   

    # --------------
    # Event handlers
    # --------------

    @inlineCallbacks
    def onStatisticsReq(self):
        try:
            lvl = yield self.config.load('logging', NAMESPACE)
            self.logLevel = lvl[NAMESPACE]
            setLogLevel(namespace=NAMESPACE, levelStr=self.logLevel)
            result = yield self.doCheckDefaults()
            if result:
                yield self.doStatistics()
            else:
                pub.sendMessage('quit', exit_code = 1)
        except Exception as e:
            log.failure('{e}',e=e)
            pub.sendMessage('quit', exit_code = 1)
        else:
            if self.next_event:
                pub.sendMessage(self.next_event)
            else:
                pub.sendMessage('quit')

    # --------------
    # Helper methods
    # --------------

    @inlineCallbacks
    def doCheckDefaults(self):
        result = True
        errors = list()
        log.debug('doCheckDefaults()')
        default_roi_id, _ = yield self.roiCtrl.getDefault()
        default_observer_id, _ = yield self.observerCtrl.getDefault()
        if default_observer_id:
            self.observer_id = int(default_observer_id)
        else:
            self.observer_id = None
            errors.append( "- No default observer defined.")
        if default_roi_id: 
            self.roi_id = int(default_roi_id)
        else:
            self.roi_id = None
            errors.append( _("- No default ROI selected.") )
        if errors:
            error_list = '\n'.join(errors)
            message = _("These things are missing:\n{0}").format(error_list)
            log.error("S{m}", m=message)
            result = False
        return(result)


    @inlineCallbacks
    def doStatistics(self):
        # Default settings extracted by doCheckDefaults()
        conditions = {'observer_id' : self.observer_id, 'roi_id': self.roi_id,}
        roi_dict = yield self.roi.loadById(conditions)
        rect = Rect.from_dict(roi_dict)
        image_id_list = yield self.sky.pending(conditions)
        N_stats = len(image_id_list)
        save_list = list()
        log.warn("Processing sky background in {N} images", N=N_stats)
        for i, (image_id,) in enumerate(image_id_list, start=1):
            name, directory, header_type, exptime, cfa_pattern, camera_id, date_id, time_id, observer_id, location_id = yield self.image.getInitialMetadata({'image_id':image_id})
            row = {
                'roi_id'     : self.roi_id,
                'image_id'   : image_id,
            }
            if self.logLevel == 'warn':
                if  (i % PAGE_SIZE) == 0:
                    log.warn("{name} ({i}/{N}) [{p}%]", i=i, N=N_stats, name=name, p=(100*i//N_stats))
            else:
                log.info("{name} ({i}/{N}) [{p}%]", i=i, N=N_stats, name=name, p=(100*i//N_stats))
            try:
                row = yield deferToThread(processImage, name, directory, roi_dict, header_type, cfa_pattern, row)
            except RAWPY_EXCEPTIONS as e:
                log.error("Corrupt {name} ({i}/{N}) [{p}%]", i=i, N=N_stats, name=name, p=(100*i//N_stats))
                yield self.image.flagAsBad(row)
                continue
            save_list.append(row)
            if (i % BUFFER_SIZE) == 0:
                log.debug("Saving to database")
                yield self.sky.save(save_list)
                save_list = list()
        if save_list:
            log.debug("Saving to database")
            yield self.sky.save(save_list)
        if N_stats:
            log.warn("Sky background processed in {n}/{d} images", n=i, d=N_stats)
        else:
            log.warn("No images to process for sky background")
        