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
import traceback

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
from azotool.cli import log, NAMESPACE

from azotool.cli.controller.observer   import ObserverController
from azotool.cli.controller.location   import LocationController
from azotool.cli.controller.camera     import CameraController
from azotool.cli.controller.sky        import SkyController
from azotool.cli.controller.image      import ImageController
from azotool.cli.controller.roi        import ROIController
from azotool.cli.controller.miscelanea import MiscelaneaController

# ----------------
# Module constants
# ----------------

# -----------------------
# Module global variables
# -----------------------

# ------------------------
# Module Utility Functions
# ------------------------

# --------------
# Module Classes
# --------------

class CommandService(Service):

    # Service name
    NAME = NAMESPACE

    def __init__(self, options, **kargs):
        super().__init__()   
        setLogLevel(namespace=NAMESPACE, levelStr='info')
        self.options = options

    #------------
    # Service API
    # ------------
    
    def startService(self):
        log.debug("Starting Command Service")
        super().startService()
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
            MiscelaneaController(
                model  = self.dbaseService.dao,
                config = self.dbaseService.dao.config,
            ),
            ImageController(
                model  = self.dbaseService.dao,
                config = self.dbaseService.dao.config,
            ),
            SkyController(
                model  = self.dbaseService.dao,
                config = self.dbaseService.dao.config,
            ),
        )
        # patch SkyBackgroundController
        self.controllers[-1].observerCtrl = self.controllers[1]
        self.controllers[-1].roiCtrl      = self.controllers[3]
        self.main()

    def stopService(self):
        log.debug("Stopping Command Service")

      
    # ==============
    # Helper methods
    # ==============

   
    def main(self):
        '''
        Command line entry point
        '''
        try:
            options = self.options
            event   = f"{options.command}_{options.subcommand}_req"
            log.debug("Sending event {ev}", ev=event)
            pub.sendMessage(event, options=options)
        except KeyboardInterrupt as e:
            log.critical("[{name}] Interrupted by user ", name=__name__)
        except Exception as e:
            log.critical("[{name}] Fatal error => {err}", name=__name__, err=str(e) )
            traceback.print_exc()
        finally:
            pass

