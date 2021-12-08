# ----------------------------------------------------------------------
# Copyright (c) 2020
#
# See the LICENSE file for details
# see the AUTHORS file for authors
# ----------------------------------------------------------------------

#--------------------
# System wide imports
# -------------------

import time
from urllib.parse import urlparse

# ---------------
# Twisted imports
# ---------------

from twisted.logger   import Logger
from twisted.internet import reactor, task
from twisted.internet.defer import inlineCallbacks
from twisted.internet.error import ConnectionRefusedError
from twisted.web.client import Agent # Support for self-signed certificates

# -------------------
# Third party imports
# -------------------

import treq
from pubsub import pub

#--------------
# local imports
# -------------

from azotea.logger  import setLogLevel
from azotea.utils.publishing import WhitelistContextFactory # Support for self-signed certificates

# ----------------
# Module constants
# ----------------

PUBLISH_PAGE_SIZE = 50

NAMESPACE = 'publi'

# -----------------------
# Module global variables
# -----------------------

log = Logger(namespace=NAMESPACE)

# ------------------------
# Module Utility Functions
# ------------------------

def sleep(delay):
    # Returns a deferred that calls do-nothing function
    # after `delay` seconds
    return task.deferLater(reactor, delay, lambda: None)



class PublishingError(Exception):
    '''Server response code was not acceptable'''
    def __str__(self):
        s = self.__doc__
        if self.args:
            s = ' {0}: {1}'.format(s, str(self.args[0]))
        s = '{0}.'.format(s)
        return s




class PublishingController:
    
    def __init__(self, model, config, next_event):
        self.model = model
        self.sky    = model.sky
        self.config = config
        self.next_event = None
        self.observerCtrl = None
        self.username = None
        self.password = None
        self.url      = None
        self.agent    = None
        setLogLevel(namespace=NAMESPACE, levelStr='info')
        pub.subscribe(self.onPublishReq, 'publishing_publish_req')


    # --------------
    # Event handlers
    # --------------

    @inlineCallbacks
    def onPublishReq(self):
        try:
            lvl = yield self.config.load('logging', NAMESPACE)
            setLogLevel(namespace=NAMESPACE, levelStr=lvl[NAMESPACE])
            result = yield self.doCheckDefaults()
            if result:
                total = yield self.sky.getPublishingCount({'observer_id': self.observer_id})
                if total == 0:
                    log.info("Publishing Processor: No Sky Brightness measurements to publish")
                else:
                    log.info("Publishing Processor: Publishing {total} measurements. This may take a while", total=total)
                    yield self.doPublish(total)
            else:
                pub.sendMessage('quit', exit_code = 1)
        except Exception as e:
            log.failure('{e}',e=e)
            pub.sendMessage('quit', exit_code = 1)
        else:
            pub.sendMessage('quit')

    # --------------
    # Helper methods
    # --------------

    @inlineCallbacks
    def getDefault(self):
        if not self.username:
            publishing_opts = yield self.config.loadSection('publishing')
            self.username  = publishing_opts['username']
            self.password  = publishing_opts['password']
            self.url       = publishing_opts['url']
            self.delay     = 1/float(publishing_opts['tps'])
            self.page_size = int(publishing_opts['page_size'])
            domain         = bytes(urlparse(self.url).hostname, 'utf-8')
            self.agent     = Agent(reactor, contextFactory=WhitelistContextFactory([domain]))


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
            errors.append("- No default observer selected.")
        if not self.username:
            errors.append("- No default publishing username defined.")
        if not self.password:
            errors.append("- No default publishing password defined.")
        if not self.url:
            errors.append("- No default publishing URL defined.")
        if errors:
            error_list = '\n'.join(errors)
            message = "These things are missing:\n{0}".format(error_list)
            log.error("Publishing Processor: {msg}", msg=message)
            result = False
        return(result)

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
            result = yield self.sky.getAll(filter_dict)
            log.info("Publishing Processor: PUBLISH page {page}, limit {limit}, size of result = {size}", page=page, limit=page_size, size=len(result))
            auth = (self.username, self.password)
            response = yield treq.post(self.url, auth=auth, json=result, timeout=30, agent=self.agent)
            log.info("{http} {status}",http=response.version, status=response.phrase)
            if not (200 <= response.code <= 299):
                failed = True; 
                message = "Server HTTP response code {0} was not acceptable".format(response.code)
                log.error("Publishing Processor: {message}", message=message)
                break
            yield sleep(self.delay)
        if not failed:
            log.info("All went good. Updating publishing state for observer id {o}",o=self.observer_id)
            yield self.sky.updatePublishingCount(filter_dict)
