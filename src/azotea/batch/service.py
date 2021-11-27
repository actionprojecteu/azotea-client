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

from azotea import FULL_VERSION_STRING
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

    def __init__(self, images_dir, depth, only_load, only_sky, only_pub, also_pub):
        super().__init__()   
        setLogLevel(namespace=NAMESPACE, levelStr='info')
        self.images_dir = images_dir
        self.depth      = depth
        self.only_load  = only_load
        self.only_sky   = only_sky
        self.only_pub   = only_pub
        self.also_pub   = also_pub

    #------------
    # Service API
    # ------------

    def startService(self):
        log.warn("{full_version}",full_version=FULL_VERSION_STRING)
        log.info("Starting Batch Service with images directory {wd}", wd=self.images_dir)
        if self.images_dir is None:
            log.error("No images directory")
            pub.sendMessage('quit', exit_code = 1)
            return
        super().startService()
        if self.only_load:
            start_event = 'images_load_req'
            next_event_img = None
            next_event_sky = None
            next_event_pub = None
        elif self.only_sky:
            start_event = 'sky_brightness_stats_req'
            next_event_img = None
            next_event_sky = None
            next_event_pub = None
        elif self.only_pub:
            start_event = 'publishing_publish_req'
            next_event_img = None
            next_event_sky = None
            next_event_pub = None
        elif self.also_pub:
            start_event = 'images_load_req'
            next_event_img = 'sky_brightness_stats_req'
            next_event_sky = 'publishing_publish_req'
            next_event_pub = None
        else:
            start_event = 'images_load_req'
            next_event_img = 'sky_brightness_stats_req'
            next_event_sky = None
            next_event_pub = None


            

        self.dbaseService = self.parent.getServiceNamed(DatabaseService.NAME)
        self.controllers = (
                CameraController(
                    model  = self.dbaseService.dao.camera,
                    config = self.dbaseService.dao.config,
                ),
                ObserverController(
                    model  = self.dbaseService.dao.observer,
                    config = self.dbaseService.dao.config,
                ),
                LocationController(
                    model  = self.dbaseService.dao.location,
                    config = self.dbaseService.dao.config,
                ),
                ROIController(
                    model  = self.dbaseService.dao.roi,
                    config = self.dbaseService.dao.config,
                ),
                ImageController(
                    model      = self.dbaseService.dao,
                    config     = self.dbaseService.dao.config,
                    next_event = next_event_img,
                ),
                SkyBackgroundController(
                    model      = self.dbaseService.dao,
                    config     = self.dbaseService.dao.config,
                    next_event = next_event_sky,
                ),
                PublishingController(
                    model      = self.dbaseService.dao,
                    config     = self.dbaseService.dao.config,
                    next_event = next_event_pub,
                ),
        )
        # Dirty monkey patching
        
        # # patch ImageController
        self.controllers[-3].cameraCtrl   = self.controllers[0]
        self.controllers[-3].observerCtrl = self.controllers[1]
        self.controllers[-3].locationCtrl = self.controllers[2]

        # patch SkyBackgroundController
        self.controllers[-2].observerCtrl = self.controllers[1]
        self.controllers[-2].roiCtrl      = self.controllers[3]

        # patch PublishingController
        self.controllers[-1].observerCtrl = self.controllers[1]

        if start_event == 'images_load_req':
            pub.sendMessage(start_event, root_dir=self.images_dir, depth=self.depth)
        else:
            pub.sendMessage(start_event)
                
        

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

