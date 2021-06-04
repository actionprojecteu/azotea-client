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
        self.sky    = model.sky
        self.config = model.config
        self.observerCtrl = None
        self._abort = False
        self.default_username = None
        self.default_password = None
        self.default_url      = None
        setLogLevel(namespace=NAMESPACE, levelStr='info')
        self.start()

    def start(self):
        log.info('starting Publishing Controller')
        pub.subscribe(self.onDetailsReq, 'publishing_details_req')
        pub.subscribe(self.onSaveReq,    'publishing_save_req')
        pub.subscribe(self.onDeleteReq,  'publishing_delete_req')
        pub.subscribe(self.onPublishReq, 'publishing_publish_req')
        pub.subscribe(self.onAbortReq,   'publishing_abort_publish_req')

    def onAbortReq(self):
        self._abort = True

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
            self.default_username = {'username': data['username']}
            self.default_password = {'password': data['password']}
            self.default_url      = {'url': data['usrl']}
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


    # We assign the default publishing options here
    @inlineCallbacks
    def getDefault(self):
        if not self.default_username:
            self.default_username = yield self.config.load('publishing','username')
        if not self.default_password:
            self.default_password = yield self.config.load('publishing','password')
        if not self.default_url:
            self.default_url = yield self.config.load('publishing','url')
        returnValue((self.default_username,  self.default_password, self.default_url))



    # Check here credentials and URL
    @inlineCallbacks
    def doCheckDefaults(self):
        result = True
        errors = list()
        default_observer_id, default_observer_details = yield self.observerCtrl.getDefault()
        if default_observer_id:
            self.observer_id = int(default_observer_id)
        else:
            self.observer_id = None
            errors.append( _("- No default observer selected.") )
        if not self.default_username:
            errors.append( _("- No default publishing username defined.") )
        if not self.default_password:
            errors.append( _("- No default publishing password defined.") )
        if not self.default_url:
            errors.append( _("- No default publishing URL defined.") )
        if errors:
            error_list = '\n'.join(errors)
            message = _("These things are missing:\n{0}").format(error_list)
            self.view.messageBoxError(who=_("Publishing Processor"),message=message)
            result = False
        returnValue(result)


    @inlineCallbacks
    def onPublishReq(self):
        self._abort = False
        result = yield self.doCheckDefaults()
        if result:
            total = yield self.sky.getPublishingCount({'observer_id': self.observer_id})
            if total == 0:
                message = _("No Sky Brightness measurements to publish")
                self.view.messageBoxInfo(who=_("Publishing Processor"),message=message)
            else:
                message = _("Publishing {0} measurements.\nThis may take a while").format(total)
                accepted = self.view.messageBoxAcceptCancel(who=_("Publishing Processor"), message=message)
                if accepted:
                    yield doPublish(total)


    @inlineCallbacks
    def doPublish(self, total):
        filter_dict = {'observer_id': self.observer_id}
        N = total // PUBLISH_PAGE_SIZE
        N = N + 1 if (total % PUBLISH_PAGE_SIZE) != 0 else N
        for page in range(N):
            filter_dict['limit']  = PUBLISH_PAGE_SIZE
            filter_dict['offset'] = page * PUBLISH_PAGE_SIZE
            result = yield publishAll(filter_dict)
            log.info("PUBLISH page {page}, limit {limit}, size of result = {size}", page=page, limit=PUBLISH_PAGE_SIZE, size=len(result))




           


