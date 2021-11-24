# ----------------------------------------------------------------------
# Copyright (c) 2020
#
# See the LICENSE file for details
# see the AUTHORS file for authors
# ----------------------------------------------------------------------

#--------------------
# System wide imports
# -------------------



# ---------------
# Twisted imports
# ---------------

from twisted.logger   import Logger
from twisted.internet.defer import inlineCallbacks

# -------------------
# Third party imports
# -------------------

from pubsub import pub
import validators

#--------------
# local imports
# -------------

from azotea.logger  import setLogLevel
from azotool.cli   import NAMESPACE, log

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

class MiscelaneaController:

    def __init__(self, model, config):
        self.model  = model
        self.config = config
        setLogLevel(namespace=NAMESPACE, levelStr='info')
        pub.subscribe(self.opticsReq,  'configure_optics_req')
        pub.subscribe(self.publishReq, 'configure_publishing_req')
        pub.subscribe(self.loggingReq, 'configure_logging_req')

    @inlineCallbacks
    def loggingReq(self, options):
        try:
            data = {}
            if options.register:
                data['regis'] = options.register
            if options.processing:
                data['sky'] = options.processing
            if options.publishing:
                data['publ'] = options.publishing
            log.info("Writting logging level configuration = {data}",data=data)
            yield self.config.saveSection('logging', data)         
        except Exception as e:
            log.failure('{e}',e=e)
            pub.sendMessage('file_quit', exit_code = 1)
        else:
            pub.sendMessage('file_quit')

    @inlineCallbacks
    def opticsReq(self, options):
        try:
            data = {
                'focal_length': options.focal_length,
                'f_number'    : options.f_number,
            }
            log.info("Writting default optics configuration = {data}",data=data)
            yield self.config.saveSection('optics', data)     
        except Exception as e:
            log.failure('{e}',e=e)
            pub.sendMessage('file_quit', exit_code = 1)
        else:
            pub.sendMessage('file_quit')

   

    @inlineCallbacks
    def publishReq(self, options):
        try:
            data = {
                'username'  : options.username,
                'password'  : options.password,
            }
            if options.url:
                valid = validators.url(options.url)
                if type(valid) == bool and valid:
                    data['url'] = options.url
                else:
                    raise ValueError(str(valid))
            log.info("Writting publishing configuration = {data}",data=data)
            yield self.config.saveSection('publishing', data)   
        except Exception as e:
            log.failure('{e}',e=e)
            pub.sendMessage('file_quit', exit_code = 1)
        else:
            pub.sendMessage('file_quit')
