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
from azotea.batch.controller.publishing import PublishingController


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

    def __init__(self, images_dir, export_opt, csv_dir, pub_flag, **kargs):
        super().__init__()   
        setLogLevel(namespace=NAMESPACE, levelStr='info')
        self.images_dir = images_dir
        self.export_opt = export_opt
        self.csv_dir = csv_dir
        self.pub_flag = pub_flag

    #------------
    # Service API
    # ------------

    def startService(self):
        log.info("Starting Batch Service with images directory {wd}", wd=self.images_dir)
        if self.images_dir is None:
            log.error("No images directory")
            pub.sendMessage('file_quit', exit_code = 1)
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
                    images_dir = self.images_dir, 
                ),
                SkyBackgroundController(
                    parent   = self, 
                    model    = self.dbaseService.dao,
                    config   = self.dbaseService.dao.config,
                    csv_dir  = self.csv_dir,
                    pub_flag = self.pub_flag,
                    export_type = self.export_opt,
                ),
                PublishingController(
                    parent   = self, 
                    model    = self.dbaseService.dao,
                    config   = self.dbaseService.dao.config,
                ),
        )
        # Dirty monkey patching
        
        # # patch ImageController
        self.controllers[-3].cameraCtrl   = self.controllers[0]
        self.controllers[-3].observerCtrl = self.controllers[1]
        self.controllers[-3].locationCtrl = self.controllers[2]

        # patch SkyBackgroundController
        self.controllers[-2].observerCtrl = self.controllers[1]
        self.controllers[-2].roiCtrl      = self.controllers[2]

        # patch PublishingController
        self.controllers[-1].observerCtrl = self.controllers[1]

        for controller in self.controllers:
            controller.start()        
        

    def stopService(self):
        log.info("Stopping Batch Service")
        

    # ---------------
    # OPERATIONAL API
    # ---------------


    # =============
    # Twisted Tasks
    # =============
   
        

      
    # ==============
    # Helper methods
    # ==============

