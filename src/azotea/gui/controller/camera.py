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

#--------------
# local imports
# -------------

from azotea import __version__
from azotea.utils.roi import Point, Rect
from azotea.logger  import setLogLevel
from azotea.utils.camera import camera_from_image

# ----------------
# Module constants
# ----------------

# Support for internationalization
_ = gettext.gettext

NAMESPACE = 'ctrl'

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

class CameraController:

    def __init__(self, parent, view, model, config):
        self.parent = parent
        self.model = model
        self.config = config
        self.view = view
        self.default_id = None
        self.default_details = None
        setLogLevel(namespace=NAMESPACE, levelStr='info')
        pub.subscribe(self.onListReq,        'camera_list_req')
        pub.subscribe(self.onDetailsReq,     'camera_details_req')
        pub.subscribe(self.onSaveReq,        'camera_save_req')
        pub.subscribe(self.onSetDefaultReq,  'camera_set_default_req')
        pub.subscribe(self.onDeleteReq,      'camera_delete_req')
        pub.subscribe(self.onChooseImageReq, 'camera_choose_image_req')

    # -------------
    # Event handler
    # -------------

    @inlineCallbacks
    def onChooseImageReq(self, path):
        try:
            info, warning = yield deferToThread(camera_from_image, path)
            if not info:
                self.view.messageBoxError(who='Preferences', message=warning)
                return
            old_info = yield self.model.load(info)    # lookup by model
            if not old_info:
                message = _("Camera not in database!")
                self.view.messageBoxWarn(who='Preferences', message=message)
            self.view.menuBar.preferences.cameraFrame.updateCameraInfoFromImage(info)
            if warning:
                self.view.messageBoxWarn(who='Preferences', message=warning)
        except Exception as e:
            log.failure('{e}',e=e)
            pub.sendMessage('quit', exit_code = 1)

    @inlineCallbacks
    def onListReq(self):
        try:
            log.debug('onListReq() fetching all unique entries from camera_t')
            info = yield self.model.loadAllNK()
            self.view.mainArea.cameraCombo.fill(info)
            preferences = self.view.menuBar.preferences
            if preferences:
                preferences.cameraFrame.listResp(info)
            # Also loads default camera
            if self.default_details:
                self.view.mainArea.cameraCombo.set(self.default_details)
                if preferences:
                    preferences.cameraFrame.detailsResp(self.default_details)
        except Exception as e:
            log.failure('{e}',e=e)
            pub.sendMessage('quit', exit_code = 1)


    @inlineCallbacks
    def onDetailsReq(self, data):
        try:
            log.info('getCamerasDetails() fetching details from camera_t given by {data}', data=data)
            info = yield self.model.load(data)
            log.info('getCamerasDetails() fetched details from camera_t returns {info}', info=info)
            self.view.menuBar.preferences.cameraFrame.detailsResp(info)
        except Exception as e:
            log.failure('{e}',e=e)
            pub.sendMessage('quit', exit_code = 1)

    @inlineCallbacks
    def onSaveReq(self, data):
        try:
            log.info('onSaveReq() insert/replace {data} details from camera_t', data=data)
            yield self.model.save(data)
            log.info('onSaveReq() insert/replace ok from camera_t')
            self.view.menuBar.preferences.cameraFrame.saveOkResp()
        except Exception as e:
            log.failure('{e}',e=e)
            pub.sendMessage('quit', exit_code = 1)


    @inlineCallbacks
    def onSetDefaultReq(self, data):
        try:
            log.info('onSetDefaultReq() getting id from camera_t given by {data}', data=data)
            info_id = yield self.model.lookup(data)
            self.default_id = info_id['camera_id']
            self.default_details = yield self.model.loadById(info_id)
            log.info('onSetDefaultReq() returned id from camera_t is {id}',id=info_id)
            log.info('onSetDefaultReq() returned details from camera_t is {d}',d=self.default_details)
            yield self.config.saveSection('camera',info_id)
            pub.sendMessage('camera_list_req')  # send a message to itself to update the views
        except Exception as e:
            log.failure('{e}',e=e)
            pub.sendMessage('quit', exit_code = 1)


    @inlineCallbacks
    def onDeleteReq(self, data):
        try:
            log.info('onDeleteReq() deleting entry from camera_t given by {data}', data=data)
            count = yield self.model.delete(data)
        except Exception as e:
            log.failure('{e}',e=e)
            self.view.menuBar.preferences.cameraFrame.deleteErrorResponse(count)
            pub.sendMessage('quit', exit_code = 1)
        else:
            yield self.onListReq()
            self.view.menuBar.preferences.cameraFrame.deleteOkResponse(count)

    # --------------
    # Helper methods
    # --------------

    @inlineCallbacks
    def getDefault(self):
        if not self.default_id:
            # loads defaults
            info = yield self.config.load('camera','camera_id')
            self.default_id = info['camera_id']
            if self.default_id:
                self.default_details = yield self.model.loadById(info)
                log.debug("getDefault() CAMERA LOADED DETAILS {d}",d=self.default_details)
        return((self.default_id,  self.default_details))
       