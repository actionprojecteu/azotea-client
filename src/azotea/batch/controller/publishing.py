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

# ---------------
# Twisted imports
# ---------------

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

from azotea.logger  import setLogLevel
from azotea.batch.controller import NAMESPACE, log

# ----------------
# Module constants
# ----------------

PUBLISH_PAGE_SIZE = 50

# -----------------------
# Module global variables
# -----------------------


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
    
    def __init__(self, model, config):
        self.model = model
        self.sky    = model.sky
        self.config = config
        self.observerCtrl = None
        self.username = None
        self.password = None
        self.url      = None
        setLogLevel(namespace=NAMESPACE, levelStr='info')
        pub.subscribe(self.onPublishReq, 'publishing_publish_req')


    # --------------
    # Event handlers
    # --------------

    @inlineCallbacks
    def onPublishReq(self):
        try:
            result = yield self.doCheckDefaults()
            if result:
                total = yield self.sky.getPublishingCount({'observer_id': self.observer_id})
                if total == 0:
                    log.info("Publishing Processor: No Sky Brightness measurements to publish")
                else:
                    log.info("Publishing Processor: Publishing {total} measurements. This may take a while", total=total)
                    yield self.doPublish(total)
            else:
                pub.sendMessage('file_quit', exit_code = 1)
        except Exception as e:
            log.failure('{e}',e=e)
            pub.sendMessage('file_quit', exit_code = 1)
        else:
            pub.sendMessage('file_quit')

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
            result = yield self.sky.publishAll(filter_dict)
            log.info("Publishing Processor: PUBLISH page {page}, limit {limit}, size of result = {size}", page=page, limit=page_size, size=len(result))
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
                    failed = True; 
                    message = "Server HTTP response code {0} was not acceptable".format(response.code)
                    break
                time.sleep(self.delay)
        if not failed:
            log.info("All went good. Updating publishing state for observer id {o}",o=self.observer_id)
            yield self.sky.updatePublishingCount(filter_dict)
            exit_code = 0
        else:
            log.error("Publishing Processor: {message}", message=message)
            exit_code = 1
        pub.sendMessage('file_quit', exit_code = exit_code)



          




           


