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

#--------------
# local imports
# -------------

from tkazotea import __version__
from tkazotea.logger  import startLogging, setLogLevel

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

class ApplicationController:

    NAME = NAMESPACE

    # Default subscription QoS
    

    def __init__(self, parent, view, model):
        self.parent = parent
        self.model = model
        self.view = view
        setLogLevel(namespace=NAMESPACE, levelStr='info')

    
    def quit(self):
        '''Returns a Deferred'''
        return self.parent.quit()

    def onDatabaseVersionReq(self):
        version = self.model.version
        self.view.menuBar.doAbout(version)

    @inlineCallbacks
    def start(self):
        log.info('starting Application Controller')
        pub.subscribe(self.quit,  'file_quit')
        pub.subscribe(self.onDatabaseVersionReq, 'database_version_req') 
        # Do some checking
        obs_id, tmp = yield self.observerCtrl.getDefault()
        loc_id, tmp = yield self.locationCtrl.getDefault()
        cam_id, tmp = yield self.cameraCtrl.getDefault()
        roi_id, tmp = yield self.roiCtrl.getDefault()
        fl, fn      = yield self.imageCtrl.getDefault()
        log.info("OBS = {k}",k=obs_id)
        log.info("LOC = {k}",k=loc_id)
        log.info("CAM = {k}",k=cam_id)
        log.info("ROI = {k}",k=roi_id)
        fl  = yield self.model.config.load(section='optics',   property='focal_length')
        fn  = yield self.model.config.load(section='optics',   property='f_number')
        if not all((obs_id, loc_id ,cam_id, roi_id ,fl['focal_length'],fn['f_number'])):
            message = "First time execution\nPlease adjust preferences!"
            self.view.messageBoxWarn('Startup',message)
        else:
            self.view.start()




       
    