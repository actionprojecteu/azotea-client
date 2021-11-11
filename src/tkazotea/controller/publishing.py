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
import time
import gettext

# ---------------
# Twisted imports
# ---------------

from twisted.logger   import Logger
from twisted.internet import  reactor, defer
from twisted.internet.defer import inlineCallbacks

from twisted.internet.error import ConnectionRefusedError

# -------------------
# Third party imports
# -------------------

import treq
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

PUBLISH_PAGE_SIZE = 50

NAMESPACE = 'CTRL '

# -----------------------
# Module global variables
# -----------------------

log = Logger(namespace=NAMESPACE)

# ------------------------
# Module Utility Functions
# ------------------------

class PublishingError(Exception):
    '''Server response code was not acceptable'''
    def __str__(self):
        s = self.__doc__
        if self.args:
            s = ' {0}: {1}'.format(s, str(self.args[0]))
        s = '{0}.'.format(s)
        return s

class PublishingController:
    
    def __init__(self, parent, view, model):
        self.parent = parent
        self.model = model
        self.view = view
        self.sky    = model.sky
        self.config = model.config
        self.observerCtrl = None
        self._abort = False
        self.username = None
        self.password = None
        self.url      = None
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
            del publishing_opts['page_size']
            del publishing_opts['tps']
            log.info('onDetailsReq() publishing = {p}',p=publishing_opts)
            self.view.menuBar.preferences.publishingFrame.detailsResp(publishing_opts)
        except Exception as e:
            log.failure('{e}',e=e)


    @inlineCallbacks
    def onSaveReq(self, data):
        try:
            log.info('onSaveReq() saving {data} defaults to config_t', data=data)
            self.username = {'username': data['username']}
            self.password = {'password': data['password']}
            self.url      = {'url'     : data['url']}
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


    @inlineCallbacks
    def getDefault(self):
        if not self.username:
            publishing_opts = yield self.config.loadSection('publishing')
            self.username  = publishing_opts['username']
            self.password  = publishing_opts['password']
            self.url       = publishing_opts['url']
            self.delay     = 1/float(publishing_opts['tps'])
            self.page_size = int(publishing_opts['page_size'])



    # Check here credentials and URL
    @inlineCallbacks
    def doCheckDefaults(self):
        result = True
        errors = list()
        yield self.getDefault()
        default_observer_id, default_observer_details = yield self.observerCtrl.getDefault()
        if default_observer_id:
            self.observer_id = int(default_observer_id)
        else:
            self.observer_id = None
            errors.append( _("- No default observer selected.") )
        if not self.username:
            errors.append( _("- No default publishing username defined.") )
        if not self.password:
            errors.append( _("- No default publishing password defined.") )
        if not self.url:
            errors.append( _("- No default publishing URL defined.") )
        if errors:
            error_list = '\n'.join(errors)
            message = _("These things are missing:\n{0}").format(error_list)
            self.parent.messageBoxError(message=message, who=_("Publishing Processor"))
            result = False
        return(result)


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
                accepted = self.parent.messageBoxAcceptCancel(message=message, who=_("Publishing Processor"))
                if accepted:
                    yield self.doPublish(total)


    @inlineCallbacks
    def doPublish(self, total):
        filter_dict = {'observer_id': self.observer_id}
        failed = False
        delay     = self.delay
        page_size = self.page_size
        N = total // page_size
        N = N + 1 if (total % page_size) != 0 else N
        for page in range(N):
            filter_dict['limit']  = page_size
            filter_dict['offset'] = page * page_size
            result = yield self.sky.publishAll(filter_dict)
            log.info("PUBLISH page {page}, limit {limit}, size of result = {size}", page=page, limit=page_size, size=len(result))
            auth = (self.username, self.password)
            try:
                response = yield treq.post(self.url, auth=auth, json=result, timeout=30)
            except ConnectionRefusedError as e:
                log.failure("Exception => {e}",e=str(e))
                failed = True; message = _("Connection refused.")
                break
            except Exception as e:
                log.failure("General Catcher. Exception {t}: {e}",t=type(e), e=str(e))
                failed = True; message = str(e)
                break
            else:
                log.info("{http} {status}",http=response.version, status=response.phrase)
                if not (200 <= response.code <= 299):
                    failed = True; message = _("Server HTTP response code {0} was not acceptable").format(response.code)
                    break
                time.sleep(self.delay)
        if not failed:
            log.info("All went good. Updating publishing state for observer id {o}",o=self.observer_id)
            yield self.sky.updatePublishingCount(filter_dict)
        else:
            self.parent.messageBoxError(who=_("Publishing Processor"), message=message)


          




           


