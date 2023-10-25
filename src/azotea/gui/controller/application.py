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
import datetime
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
from azotea.logger  import startLogging, setLogLevel

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

class ApplicationController:

    NAME = NAMESPACE

    # Default subscription QoS
    

    def __init__(self, parent, view, model):
        self.parent = parent
        self.model = model
        self.view = view
        setLogLevel(namespace=NAMESPACE, levelStr='info')
        pub.subscribe(self.onDatabaseVersionReq, 'database_version_req')
        pub.subscribe(self.onCheckPreferencesReq, 'check_preferences_req')
        pub.subscribe(self.onSaveConsentReq, 'save_consent_req')
        pub.subscribe(self.onBootReq, 'bootstrap_req')


    # --------------
    # Event handlers
    # --------------

    def onDatabaseVersionReq(self):
        try:
            version = self.model.version
            uuid    = self.model.uuid
            self.view.menuBar.doAbout(version, uuid)
        except Exception as e:
            log.failure('{e}',e=e)
            pub.sendMessage('quit', exit_code = 1)

    @inlineCallbacks
    def onCheckPreferencesReq(self):
        try:
            # Do some checking
            obs_id, tmp = yield self.observerCtrl.getDefault()
            loc_id, tmp = yield self.locationCtrl.getDefault()
            cam_id, tmp = yield self.cameraCtrl.getDefault()
            roi_id, tmp = yield self.roiCtrl.getDefault()
            fl, fn      = yield self.imageCtrl.getDefault()
            log.debug("OBS = {k}",k=obs_id)
            log.debug("LOC = {k}",k=loc_id)
            log.debug("CAM = {k}",k=cam_id)
            log.debug("ROI = {k}",k=roi_id)
            fl  = yield self.model.config.load(section='optics',   property='focal_length')
            fn  = yield self.model.config.load(section='optics',   property='f_number')
            if not all((obs_id, loc_id ,cam_id, roi_id ,fl['focal_length'],fn['f_number'])):
                message = "First time execution\nPlease adjust preferences!"
                self.view.messageBoxWarn(who='Startup', message=message)
            else:
                self.view.start()
        except Exception as e:
            log.failure('{e}',e=e)
            pub.sendMessage('quit', exit_code = 1)


    @inlineCallbacks
    def onSaveConsentReq(self):
        try:
            now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            yield self.model.config.save(section='gdpr', property='agree', value='Yes')
            yield self.model.config.save(section='gdpr', property='tstamp', value=now)
            yield self.onCheckPreferencesReq()
        except Exception as e:
            log.failure('{e}',e=e)
            pub.sendMessage('quit', exit_code = 1)


    @inlineCallbacks
    def onBootReq(self):
        try:
            log.info('starting Application Controller')
            consent  = yield self.model.config.load(section='gdpr', property='agree')
            if not consent:
                self.view.openConsentDialog()
            else:
                pub.sendMessage('check_preferences_req')
        except Exception as e:
            log.failure('{e}',e=e)
            pub.sendMessage('quit', exit_code = 1)

       

       
    