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
from twisted.internet.defer import inlineCallbacks

# -------------------
# Third party imports
# -------------------

from pubsub import pub

#--------------
# local imports
# -------------

from azotea.logger  import setLogLevel

# ----------------
# Module constants
# ----------------

# Support for internationalization
_ = gettext.gettext

NAMESPACE = 'ctrl'

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
        pub.subscribe(self.onDetailsReq, 'misc_details_req')
        pub.subscribe(self.onSaveReq,    'misc_save_req')
        pub.subscribe(self.onDeleteReq,  'misc_delete_req')

    # --------------
    # Event handlers
    # --------------

    @inlineCallbacks
    def onDetailsReq(self):
        try:
            log.debug('onDetailsReq() fetching optics from config_t')
            optics_opts = yield self.model.config.loadSection(section='optics')
            log.info('onDetailsReq() optics = {o}',o=optics_opts)
            self.view.menuBar.preferences.miscelaneaFrame.detailsResp(optics_opts)
        except Exception as e:
            log.failure('{e}',e=e)
            pub.sendMessage('quit', exit_code = 1)


    def onSaveReq(self, data):
        try:
            log.debug('onSaveReq() saving {data} defaults to config_t', data=data)
            pub.sendMessage('images_set_default_optics_req', data=data)
            log.debug('onSaveReq() saved {data} defaults to config_t', data=data)
            self.view.menuBar.preferences.miscelaneaFrame.saveOkResp()
        except Exception as e:
            log.failure('{e}',e=e)
            pub.sendMessage('quit', exit_code = 1)


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
            pub.sendMessage('quit', exit_code = 1)
        else:
            self.view.menuBar.preferences.miscelaneaFrame.deleteOkResponse(count)

