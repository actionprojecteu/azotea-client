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
import glob


# ---------------
# Twisted imports
# ---------------

from twisted.application.service import Service
from twisted.logger import Logger


from twisted.internet import reactor, task, defer
from twisted.internet.defer import inlineCallbacks
from twisted.internet.threads import deferToThread

# -------------------
# Third party imports
# -------------------

from pubsub import pub

#--------------
# local imports
# -------------

from azotea.logger import setLogLevel
from azotea.dbase.service   import DatabaseService
from azotea.batch.controller.image    import ImageController
from azotea.batch.controller.sky      import SkyBackgroundController
from azotea.batch.controller.camera   import CameraController
from azotea.batch.controller.observer import ObserverController
from azotea.batch.controller.location import LocationController
from azotea.batch.controller.roi      import ROIController

# ----------------
# Module constants
# ----------------

NAMESPACE = 'batch'

# -----------------------
# Module global variables
# -----------------------

log = Logger(NAMESPACE)

# ------------------------
# Module Utility Functions
# ------------------------

# --------------
# Module Classes
# --------------

class BatchService(Service):

    # Service name
    NAME = NAMESPACE

    def __init__(self, work_dir, **kargs):
        super().__init__()   
        setLogLevel(namespace=NAMESPACE, levelStr='info')
        self.work_dir = work_dir

    #------------
    # Service API
    # ------------

    def startService(self):
        log.info("Starting Batch Service with working directory {wd}", wd=self.work_dir)
        if self.work_dir is None:
            log.error("No working directory")
            pub.sendMessage('file_quit')
            return
        
        super().startService()
        self.dbaseService = self.parent.getServiceNamed(DatabaseService.NAME)
        self.controllers = (
                CameraController(
                    parent = self, 
                    model  = self.dbaseService.dao.camera,
                    config = self.dbaseService.dao.config,
                ),
                ObserverController(
                    parent = self, 
                    model  = self.dbaseService.dao.observer,
                    config = self.dbaseService.dao.config,
                ),
                LocationController(
                    parent = self, 
                    model  = self.dbaseService.dao.location,
                    config = self.dbaseService.dao.config,
                ),
                ROIController(
                    parent = self, 
                    model  = self.dbaseService.dao.roi,
                    config = self.dbaseService.dao.config,
                ),
                ImageController(
                    parent   = self, 
                    model    = self.dbaseService.dao,
                    config   = self.dbaseService.dao.config,
                    work_dir = self.work_dir, 
                ),
                SkyBackgroundController(
                    parent   = self, 
                    model    = self.dbaseService.dao,
                    config   = self.dbaseService.dao.config,
                ),
        )
        # Dirty monkey patching
        
        # # patch ImageController
        self.controllers[-2].cameraCtrl   = self.controllers[0]
        self.controllers[-2].observerCtrl = self.controllers[1]
        self.controllers[-2].locationCtrl = self.controllers[2]

        # # patch SkyBackgroundController
        self.controllers[-1].observerCtrl = self.controllers[1]
        self.controllers[-1].roiCtrl      = self.controllers[2]

        for controller in self.controllers:
            controller.start()        
        

    def stopService(self):
        log.info("Stopping Batch Service")
        

    # ---------------
    # OPERATIONAL API
    # ---------------

    def quit(self):
        pub.sendMessage('file_quit')

    # =============
    # Twisted Tasks
    # =============
   
        

      
    # ==============
    # Helper methods
    # ==============

