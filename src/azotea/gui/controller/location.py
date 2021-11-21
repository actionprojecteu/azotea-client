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
from twisted.internet.defer import inlineCallbacks
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

from azotea import __version__
from azotea.utils.roi import Point, Rect
from azotea.logger  import startLogging, setLogLevel
from azotea.error import TooDifferentValuesBiasError, NotPowerOfTwoErrorBiasError
from azotea.utils.location import randomize

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


# --------------
# Module Classes
# --------------

class LocationController:

    def __init__(self, parent, view, model, config):
        self.parent = parent
        self.model = model
        self.view = view
        self.config = config
        self.default_id = None
        self.default_details = None
        setLogLevel(namespace=NAMESPACE, levelStr='info')
        pub.subscribe(self.onListReq,       'location_list_req')
        pub.subscribe(self.onDetailsReq,    'location_details_req')
        pub.subscribe(self.onSaveReq,       'location_save_req')
        pub.subscribe(self.onSetDefaultReq, 'location_set_default_req')
        pub.subscribe(self.onDeleteReq,     'location_set_delete_req')

   
    
    # --------------   
    # Event handlers
    # --------------

    @inlineCallbacks
    def onListReq(self):
        try:
            log.debug('onListReq() fetching all unique entries from location_t')
            info = yield self.model.loadAllNK()
            self.view.mainArea.locationCombo.fill(info)
            preferences = self.view.menuBar.preferences
            if preferences:
                preferences.locationFrame.listResp(info)
            # Also shows default location
            if self.default_details:
                self.view.mainArea.locationCombo.set(self.default_details)
                if preferences:
                    preferences.locationFrame.detailsResp(self.default_details)
        except Exception as e:
            log.failure('{e}',e=e)
            pub.sendMessage('file_quit', exit_code = 1)

    @inlineCallbacks
    def onDetailsReq(self, data):
        try:
            log.info('onDetailsReq() fetching details from location_t given by {data}', data=data)
            info = yield self.model.load(data)
            log.info('onDetailsReq() fetched details from location_t returns {info}', info=info)
            self.view.menuBar.preferences.locationFrame.detailsResp(info)
        except Exception as e:
            log.failure('{e}',e=e)
            pub.sendMessage('file_quit', exit_code = 1)


    @inlineCallbacks
    def onSaveReq(self, data):
        try:
            log.info('onSaveReq() analyze {data} details from location_t', data=data)
            # look for previously saved location with the same site_name and location
            previous = yield self.model.load(data)
            if not previous:
                yield self.writeRandomized(data)
                log.info('onSaveReq() insert ok from location_t')
            elif previous['randomized'] == 1 and data['randomized']:
                previous['utc_offset'] = data['utc_offset']
                log.info('updated previous location_t: {data}', data=previous)
                yield self.model.save(previous)
                log.info('onSaveReq() insert ok from location_t')
            else:
                yield self.writeRandomized(data)
                log.info('onSaveReq() insert ok from location_t')
            self.view.menuBar.preferences.locationFrame.saveOkResp()
        except Exception as e:
            log.failure('{e}',e=e)
            pub.sendMessage('file_quit', exit_code = 1)


    @inlineCallbacks
    def onSetDefaultReq(self, data):
        try:
            log.info('onSetDefaultReq() geting id from location_t given by {data}', data=data)
            info_id = yield self.model.lookup(data)
            self.default_id = info_id['location_id']
            self.default_details = yield self.model.loadById(info_id)
            log.info('onSetDefaultReq() returned id from location_t is {id}',id=info_id)
            log.info('onSetDefaultReq() returned details from location_t is {d}',d=self.default_details)
            yield self.config.saveSection('location',info_id)
            pub.sendMessage('location_list_req')  # send a message to itself to update the views
        except Exception as e:
            log.failure('{e}',e=e)
            pub.sendMessage('file_quit', exit_code = 1)


    @inlineCallbacks
    def onDeleteReq(self, data):
        try:
            log.info('onDeleteReq() deleting all entries from location_t given by {data}', data=data)
            count = yield self.model.delete(data)
        except Exception as e:
            log.failure('{e}',e=e)
            self.view.menuBar.preferences.locationFrame.deleteErrorResponse()
            pub.sendMessage('file_quit', exit_code = 1)
        else:
            yield self.onListReq()
            self.view.menuBar.preferences.locationFrame.deleteOkResponse(count)


    # -------------
    # Helper methods
    # --------------

    @inlineCallbacks
    def getDefault(self):
        if not self.default_id:
            # loads defaults
            info = yield self.config.load('location','location_id')
            self.default_id = info['location_id']
            if self.default_id:
                self.default_details = yield self.model.loadById(info)
        return((self.default_id,  self.default_details))

    @inlineCallbacks
    def writeRandomized(self, data):
        longitude = data['longitude'] 
        latitude  = data['latitude'] 
        randomizeFlag = data['randomized']
        if longitude and latitude and randomizeFlag:
            long1 = longitude; lat1 = latitude
            longitude, latitude = randomize(longitude, latitude)
            log.info('Randomized coordinates ({long1}, {lat1}) -> ({long2}, {lat2})', 
                long1=long1, lat1=lat1, long2=longitude, lat2=latitude)
        data['longitude'] = longitude
        data['latitude']  = latitude
        log.info('Insert to location_t: {data}', data=data)
        yield self.model.save(data)
