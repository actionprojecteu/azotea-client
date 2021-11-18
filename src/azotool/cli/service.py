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

from azotool.cli.controller.observer import ObserverController

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
        log.info("Starting Command Service")
        
        super().startService()
        self.dbaseService = self.parent.getServiceNamed(DatabaseService.NAME)
        self.controllers = (
            ObserverController(
                parent = self, 
                model  = self.dbaseService.dao.observer,
                config = self.dbaseService.dao.config,
            ),
        )
        for controller in self.controllers:
            controller.start()    
        self.main()    
        

    def stopService(self):
        log.info("Stopping Command Service")
        

    # ---------------
    # OPERATIONAL API
    # ---------------


    # =============
    # Twisted Tasks
    # =============
   
        

      
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
            log.info("Sending event {ev}", ev=event)
            pub.sendMessage(event, options=options)
        except KeyboardInterrupt as e:
            log.critical("[{name}] Interrupted by user ", name=__name__)
        except Exception as e:
            log.critical("[{name}] Fatal error => {err}", name=__name__, err=str(e) )
            traceback.print_exc()
        finally:
            pass

