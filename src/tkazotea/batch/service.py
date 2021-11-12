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

from tkazotea.logger import setLogLevel

# ----------------
# Module constants
# ----------------

NAMESPACE = 'BATCH'

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
            self.quit()
        else:
            super().startService()
        

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

