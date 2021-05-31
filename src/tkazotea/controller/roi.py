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
import math
import gettext

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
import exifread
import rawpy

#--------------
# local imports
# -------------

from tkazotea import __version__
from tkazotea.utils import Rect, Point
from tkazotea.logger  import startLogging, setLogLevel
from tkazotea.error import TooDifferentValuesBiasError, NotPowerOfTwoErrorBiasError

# ----------------
# Module constants
# ----------------

# Support for internationalization
_ = gettext.gettext

NAMESPACE = 'CTRL '

# -----------------------
# Module global variables
# -----------------------

log = Logger(namespace=NAMESPACE)

# ------------------------
# Module Utility Functions
# ------------------------

def reshapeRect(filename, rect):
        log.debug('Loading EXIF metadata from {f}',f=filename)
        with open(filename, 'rb') as f:
            exif = exifread.process_file(f, details=False)
        if not exif:
            log.warn('Could not open EXIF metadata',filename)
            return dict()
        # Get the real RAW dimensions instead
        with rawpy.imread(filename) as img:
            imageHeight, imageWidth = img.raw_image.shape
        imageHeight = imageHeight //2 # From raw dimensions without debayering
        imageWidth =  imageWidth //2  # to dimensions we actually handle
        width, height = rect.dimensions()
        center=Point(imageWidth//2,imageHeight//2)
        x1 = (imageWidth  -  width)//2
        y1 = (imageHeight - height)//2
        rect += Point(x1,y1)  # Shift ROI using this (x1,y1) point
        result = rect.to_dict()
        result['display_name'] = str(rect)
        result['comment'] = _("ROI for {0}, centered at P={1}, width={2}, height={3}").format(str(exif.get('Image Model')),center,width,height)
        return result



# --------------
# Module Classes
# --------------


class ROIController:

    def __init__(self, parent, view, model, config):
        self.parent = parent
        self.model = model
        self.view = view
        self.config = config
        self.default_id = None
        self.default_details = None
        setLogLevel(namespace=NAMESPACE, levelStr='info')
    
   
    def start(self):
        log.info('starting ROI Controller')
        pub.subscribe(self.onListReq,         'roi_list_req')
        pub.subscribe(self.onDetailsReq,      'roi_details_req')
        pub.subscribe(self.onSaveReq,         'roi_save_req')
        pub.subscribe(self.onSetDefaultReq,   'roi_set_default_req')
        pub.subscribe(self.onDeleteReq,       'roi_delete_req')
        pub.subscribe(self.onSetAutomaticReq, 'roi_set_automatic_req')


    @inlineCallbacks
    def getDefault(self):
        if not self.default_id:
            # loads defaults
            info = yield self.config.load('ROI','roi_id')
            self.default_id = info['roi_id']
            if self.default_id:
                self.default_details = yield self.model.loadById(info)
        returnValue((self.default_id,  self.default_details))


    @inlineCallbacks
    def onListReq(self):
        try:
            log.info('onListReq() fetching all unique entries from roi_t')
            info = yield self.model.loadAllNK()
            self.view.mainArea.ROICombo.fill(info)
            preferences = self.view.menuBar.preferences
            if preferences:
                preferences.roiFrame.listResp(info) 
            # Also shows default ROI
            if self.default_details:
                self.view.mainArea.ROICombo.set(self.default_details)
                if preferences:
                    preferences.roiFrame.detailsResp(self.default_details)

        except Exception as e:
            log.failure('{e}',e=e)

    @inlineCallbacks
    def onDetailsReq(self, data):
        try:
            log.debug('onDetailsReq() fetching details from roi_t given by {data}', data=data)
            info = yield self.model.load(data)
            log.debug('onDetailsReq() fetched details from roi_t returns {info}', info=info)
            self.view.menuBar.preferences.roiFrame.detailsResp(info)
        except Exception as e:
            log.failure('{e}',e=e)


    @inlineCallbacks
    def onSaveReq(self, data):
        try:
            log.debug('onSaveReq() insert/replace {data} details from roi_t', data=data)
            data['display_name'] = str(Rect.from_dict(data))
            yield self.model.save(data)
            log.debug('onSaveReq() insert/replace ok from roi_t')
            self.view.menuBar.preferences.roiFrame.saveOkResp()
        except Exception as e:
            log.failure('{e}',e=e)


    @inlineCallbacks
    def onSetDefaultReq(self, data):
        try:
            log.info('onSetDefaultReq() geting id from roi_t given by {data}', data=data)
            info_id = yield self.model.lookup(data)
            self.default_id = info_id['roi_id']
            self.default_details = yield self.model.loadById(info_id)
            log.info('onSetDefaultReq() returned id from roi_t is {id}',id=info_id)
            log.info('onSetDefaultReq() returned details from roi_t is {d}',d=self.default_details)
            yield self.config.saveSection('ROI',info_id)
            pub.sendMessage('roi_list_req')  # send a message to itself to update the views
        except Exception as e:
            log.failure('{e}',e=e)


    @inlineCallbacks
    def onDeleteReq(self, data):
        try:
            log.debug('onDeleteReq() deleting entry from roi_t given by {data}', data=data)
            count = yield self.model.delete(data)
        except Exception as e:
            log.failure('{e}',e=e)
            self.view.menuBar.preferences.roiFrame.deleteErrorResponse(count)
        yield self.onListReq()
        self.view.menuBar.preferences.roiFrame.deleteOkResponse(count)

    @inlineCallbacks
    def onSetAutomaticReq(self, filename, rect):
        info = yield deferToThread(reshapeRect, filename, rect)
        log.debug('onSetAutomaticReq() returns {info}', info=info)
        self.view.menuBar.preferences.roiFrame.automaticROIResp(info)
