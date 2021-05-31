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
from twisted.internet.threads import deferToThread

# -------------------
# Third party imports
# -------------------

from pubsub import pub
import exifread
import rawpy

#--------------
# local imports
# -------------

from tkazotea import __version__
from tkazotea.utils import Point, Rect
from tkazotea.logger  import startLogging, setLogLevel
from tkazotea.error import TooDifferentValuesBiasError, NotPowerOfTwoErrorBiasError

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


class MiscelaneaController:
    
    def __init__(self, parent, view, model):
        self.parent = parent
        self.model = model
        self.view = view
        setLogLevel(namespace=NAMESPACE, levelStr='info')
    
    def start(self):
        log.info('starting Miscelanea Controller')
        pub.subscribe(self.onDetailsReq, 'misc_details_req')
        pub.subscribe(self.onSaveReq,    'misc_save_req')
        pub.subscribe(self.onDeleteReq,  'misc_delete_req')

    @inlineCallbacks
    def onDetailsReq(self):
        try:
            log.debug('onDetailsReq() fetching optics from config_t')
            optics_opts = yield self.model.config.loadSection(section='optics')
            log.info('onDetailsReq() optics = {o}',o=optics_opts)
            self.view.menuBar.preferences.miscelaneaFrame.detailsResp(optics_opts)
        except Exception as e:
            log.failure('{e}',e=e)


    @inlineCallbacks
    def onSaveReq(self, data):
        try:
            log.debug('onSaveReq() saving {data} defaults to config_t', data=data)
            pub.sendMessage('images_set_default_optics_req', data=data)
            log.debug('onSaveReq() saved {data} defaults to config_t', data=data)
            self.view.menuBar.preferences.miscelaneaFrame.saveOkResp()
        except Exception as e:
            log.failure('{e}',e=e)


    @inlineCallbacks
    def onDeleteReq(self, data):
        try:
            log.debug('onDeleteReq() deleting entries from config_t given by {data}', data=data)
            count = yield self.model.config.deleteSection('optics',data)
            log.debug('onDeleteReq() set config entries to NULL', data=data)
            yield self.onDetailsReq()
        except Exception as e:
            log.failure('{e}',e=e)
            self.view.menuBar.preferences.miscelaneaFrame.deleteErrorResponse(count)
        self.view.menuBar.preferences.miscelaneaFrame.deleteOkResponse(count)

