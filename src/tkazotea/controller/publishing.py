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
import math
import gettext

# ---------------
# Twisted imports
# ---------------

from twisted.logger   import Logger
from twisted.internet import  reactor, defer
from twisted.internet.defer import inlineCallbacks, returnValue

# -------------------
# Third party imports
# -------------------

from pubsub import pub

#--------------
# local imports
# -------------

from tkazotea.logger  import setLogLevel

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


class PublishingController:
    
    def __init__(self, parent, view, model):
        self.parent = parent
        self.model = model
        self.view = view
        setLogLevel(namespace=NAMESPACE, levelStr='info')
    
    def start(self):
        log.info('starting Publishing Controller')
        pub.subscribe(self.onDetailsReq, 'publishing_details_req')
        pub.subscribe(self.onSaveReq,    'publishing_save_req')
        pub.subscribe(self.onDeleteReq,  'publishing_delete_req')

    @inlineCallbacks
    def onDetailsReq(self):
        try:
            log.info('onDetailsReq() fetching publishing from config_t')
            publishing_opts = yield self.model.config.loadSection(section='publishing')
            log.info('onDetailsReq() publishing = {p}',p=publishing_opts)
            self.view.menuBar.preferences.publishingFrame.detailsResp(publishing_opts)
        except Exception as e:
            log.failure('{e}',e=e)


    @inlineCallbacks
    def onSaveReq(self, data):
        try:
            log.info('onSaveReq() saving {data} defaults to config_t', data=data)
            yield self.model.config.saveSection('publishing', data)
            log.info('onSaveReq() saved {data} defaults to config_t', data=data)
            self.view.menuBar.preferences.publishingFrame.saveOkResp()
        except Exception as e:
            log.failure('{e}',e=e)


    @inlineCallbacks
    def onDeleteReq(self, data):
        try:
            log.info('onDeleteReq() deleting entries from config_t given by {data}', data=data)
            count = yield self.model.config.deleteSection('publishing',data)
            log.info('onDeleteReq() set config entries to NULL', data=data)
            yield self.onDetailsReq()
        except Exception as e:
            log.failure('{e}',e=e)
            self.view.menuBar.preferences.publishingFrame.deleteErrorResponse(count)
        self.view.menuBar.preferences.publishingFrame.deleteOkResponse(count)

