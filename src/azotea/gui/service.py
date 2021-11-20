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

# -------------------
# Third party imports
# -------------------

from pubsub import pub

# ---------------
# Twisted imports
# ---------------

from twisted.logger   import Logger
from twisted.internet import  tksupport, reactor, defer, task
from twisted.application.service import Service
from twisted.internet.defer import inlineCallbacks



#--------------
# local imports
# -------------


from azotea.logger  import setLogLevel
from azotea.dbase.service   import DatabaseService
from azotea.gui.application import Application
from azotea.gui.controller.application import ApplicationController
from azotea.gui.controller.camera      import CameraController
from azotea.gui.controller.observer    import ObserverController
from azotea.gui.controller.location    import LocationController
from azotea.gui.controller.roi         import ROIController
from azotea.gui.controller.miscelanea  import MiscelaneaController
from azotea.gui.controller.image       import ImageController
from azotea.gui.controller.sky         import SkyBackgroundController
from azotea.gui.controller.publishing  import PublishingController


# ----------------
# Module constants
# ----------------

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

class GraphicalService(Service):

    NAME = NAMESPACE

    # Default subscription QoS
    

    def __init__(self, **kargs):
        super().__init__()
        setLogLevel(namespace=NAMESPACE, levelStr='info')
        self.task    = task.LoopingCall(self.heartBeat)

    # -----------
    # Service API
    # -----------
    
    def startService(self):
        log.info('starting Graphical User Interface')
        super().startService()
        self.application = Application()
        self.dbaseService = self.parent.getServiceNamed(DatabaseService.NAME)
        self.controllers = (
            ApplicationController(
                parent  = self, 
                view    = self.application, 
                model   = self.dbaseService.dao,
            ),
            CameraController(
                parent = self, 
                view   = self.application, 
                model  = self.dbaseService.dao.camera,
                config = self.dbaseService.dao.config,
            ),
            ObserverController(
                parent = self, 
                view   = self.application, 
                model  = self.dbaseService.dao.observer,
                config = self.dbaseService.dao.config,
            ),
            LocationController(
                parent = self, 
                view   = self.application, 
                model  = self.dbaseService.dao.location,
                config = self.dbaseService.dao.config,
            ),
            ROIController(
                parent = self, 
                view   = self.application, 
                model  = self.dbaseService.dao.roi,
                config = self.dbaseService.dao.config,
            ),
            MiscelaneaController(
                parent = self, 
                view   = self.application, 
                model  = self.dbaseService.dao,
            ),
            ImageController(
                parent = self, 
                view   = self.application, 
                model  = self.dbaseService.dao,
            ),
            SkyBackgroundController(
                parent       = self, 
                view         = self.application, 
                model        = self.dbaseService.dao,
            ),
            PublishingController(
                parent       = self, 
                view         = self.application, 
                model        = self.dbaseService.dao,
            )
        )
        # Dirty monkey patching
        # patch ApplicationController
        self.controllers[0].cameraCtrl    = self.controllers[1]
        self.controllers[0].observerCtrl  = self.controllers[2]
        self.controllers[0].locationCtrl  = self.controllers[3]
        self.controllers[0].roiCtrl       = self.controllers[4]
        self.controllers[0].imageCtrl     = self.controllers[6]

        # patch ImageController
        self.controllers[-3].cameraCtrl   = self.controllers[1]
        self.controllers[-3].observerCtrl = self.controllers[2]
        self.controllers[-3].locationCtrl = self.controllers[3]

        # patch SkyBackgroundController
        self.controllers[-2].observerCtrl = self.controllers[2]
        self.controllers[-2].roiCtrl      = self.controllers[4]

        # patch PublishingController
        self.controllers[-1].observerCtrl = self.controllers[2]     

        tksupport.install(self.application)
        self.task.start(3, now=False) # call every T seconds
        # Start application controller 
        pub.sendMessage('bootstrap_req')

    def stopService(self):
        log.info('Stopping Graphical User Interface Service')
        self.task.stop()
        return super().stopService()


    # ---------
    # Heartbeat
    # ---------

    def heartBeat(self):
        '''Oly for dubugging purposes'''
        log.info('Tick')