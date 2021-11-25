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

from azotea import __version__
from azotea.utils.roi import Point, Rect
from azotea.logger  import startLogging, setLogLevel

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

# --------------
# Module Classes
# --------------

class ObserverController:

    def __init__(self, parent, view, model, config):
        self.parent = parent
        self.model = model
        self.view = view
        self.config = config
        self.default_id = None
        self.default_details = None
        setLogLevel(namespace=NAMESPACE, levelStr='info')
        pub.subscribe(self.onListReq,       'observer_list_req')
        pub.subscribe(self.onDetailsReq,    'observer_details_req')
        pub.subscribe(self.onSaveReq,       'observer_save_req')
        pub.subscribe(self.onSetDefaultReq, 'observer_set_default_req')
        pub.subscribe(self.onDeleteReq,     'observer_delete_req')
        pub.subscribe(self.onPurgeReq,      'observer_purge_req')

    # --------------
    # Event handlers
    # --------------

    @inlineCallbacks
    def onListReq(self):
        try:
            log.debug('onListReq() fetching all unique entries from observer_t')
            info = yield self.model.loadAllNK()
            self.view.mainArea.observerCombo.fill(info)
            preferences = self.view.menuBar.preferences
            if preferences:
                preferences.observerFrame.listResp(info)
            # Also loads default observer
            if self.default_details:
                self.view.mainArea.observerCombo.set(self.default_details)
                if preferences:
                    preferences.observerFrame.detailsResp(self.default_details)
        except Exception as e:
            log.failure('{e}',e=e)
            pub.sendMessage('file_quit', exit_code = 1)


    @inlineCallbacks
    def onDetailsReq(self, data):
        try:
            log.info('onDetailsReq() fetching details from observer_t given by {data}', data=data)
            info = yield self.model.load(data)
            log.info('onDetailsReq() fetched details from observer_t returns {info}', info=info)
            self.view.menuBar.preferences.observerFrame.detailsResp(info)
        except Exception as e:
            log.failure('{e}',e=e)
            pub.sendMessage('file_quit', exit_code = 1)


    @inlineCallbacks
    def onSaveReq(self, data):
        try:
            log.info('onSaveReq() versioned insert {data} details from observer_t', data=data)
            yield self.model.save(data)
            log.info('onSaveReq() versioned insert ok from observer_t')
            self.view.menuBar.preferences.observerFrame.saveOkResp()
        except Exception as e:
            log.failure('{e}',e=e)
            pub.sendMessage('file_quit', exit_code = 1)


    @inlineCallbacks
    def onSetDefaultReq(self, data):
        try:
            log.info('onSetDefaultReq() getting id from observer_t given by {data}', data=data)
            info_id = yield self.model.lookup(data)
            self.default_id = info_id['observer_id']
            self.default_details = yield self.model.loadById(info_id)
            log.info('onSetDefaultReq() returned id from observer_t is {id}',id=info_id)
            log.info('onSetDefaultReq() returned details from observer_t is {d}',d=self.default_details)
            yield self.config.saveSection('observer',info_id)
            pub.sendMessage('observer_list_req')  # send a message to itself to update the views
        except Exception as e:
            log.failure('{e}',e=e)
            pub.sendMessage('file_quit', exit_code = 1)


    @inlineCallbacks
    def onDeleteReq(self, data):
        try:
            log.info('onDeleteReq() deleting all entries from observer_t given by {data}', data=data)
            count = yield self.model.delete(data)
        except Exception as e:
            log.failure('{e}',e=e)
            self.view.menuBar.preferences.observerFrame.deleteErrorResponse()
            pub.sendMessage('file_quit', exit_code = 1)
        else:
            yield self.onListReq()
            self.view.menuBar.preferences.observerFrame.deleteOkResponse(count)


    @inlineCallbacks
    def onPurgeReq(self, data):
        try:
            log.debug('onPurgeReq() deleting expired entries from observer_t given by {data}', data=data)
            count = yield self.model.deleteVersions(data)
        except Exception as e:
            log.failure('{e}',e=e)
            self.view.menuBar.preferences.observerFrame.purgeErrorResponse()
            pub.sendMessage('file_quit', exit_code = 1)
        else:
            self.view.menuBar.preferences.observerFrame.purgeOkResponse(count)

    # --------------
    # Helper methods
    # --------------

    @inlineCallbacks
    def getDefault(self):
        if not self.default_id:
            # loads defaults
            info = yield self.config.load('observer','observer_id')
            self.default_id = info['observer_id']
            if self.default_id:
                self.default_details = yield self.model.loadById(info)
        return((self.default_id,  self.default_details))

