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

# ---------------
# Twisted imports
# ---------------

from twisted.logger   import Logger
from twisted.internet import  tksupport, reactor, defer, task
from twisted.application.service import Service
from twisted.internet.defer import inlineCallbacks

# -------------------
# Third party imports
# -------------------

from pubsub import pub

#--------------
# local imports
# -------------


from tkazotea.logger  import setLogLevel
from tkazotea.dbase.service   import DatabaseService
from tkazotea.gui.application import Application
from tkazotea.controller.application import ApplicationController
from tkazotea.controller.camera      import CameraController
from tkazotea.controller.observer    import ObserverController
from tkazotea.controller.location    import LocationController
from tkazotea.controller.roi         import ROIController
from tkazotea.controller.miscelanea  import MiscelaneaController
from tkazotea.controller.image       import ImageController
from tkazotea.controller.sky         import SkyBackgroundController
from tkazotea.controller.publishing  import PublishingController


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


    @inlineCallbacks
    def quit(self):
         yield self.parent.stopService()
         reactor.stop()


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

        for controller in self.controllers[1:]:
            controller.start()        

        tksupport.install(self.application)
        self.task.start(3, now=False) # call every T seconds
        # Start application controller a bit later
        reactor.callLater(0, self.controllers[0].start)
        

    def stopService(self):
        log.info('stopping Graphical User Interface Service')
        self.task.stop()
        return super().stopService()


    # -----------------
    # Configuration API
    # -----------------

    def configure(self, **kwargs):
        '''Configuration from command line arguments'''
        pass

    # ---------
    # Heartbeat
    # ---------

    def heartBeat(self):
        '''Oly for dubugging purposes'''
        log.info('Tick')