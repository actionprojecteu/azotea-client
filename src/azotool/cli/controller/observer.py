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

class ObserverController:

    def __init__(self, model, config):
        self.model  = model
        self.config = config
        setLogLevel(namespace=NAMESPACE, levelStr='info')
        pub.subscribe(self.createReq,  'observer_create_req')

    @inlineCallbacks
    def createReq(self, options):
        data = {
            'family_name': ' '.join(options.name),
            'surname'    : ' '.join(options.surname),
            'affiliation': ' '.join(options.affiliation),
            'acronym'    : ' '.join(options.acronym),
        }
        try:
            log.info('Versioned insert to observer_t: {data}', data=data)
            yield self.model.save(data)
            log.debug('Getting id from observer_t')
            info_id = yield self.model.lookup(data)
            log.info('Setting default observer in configuration section as id = {id}',id=info_id)
            yield self.config.saveSection('observer',info_id)
        except Exception as e:
            log.failure('{e}',e=e)
            pub.sendMessage('file_quit', exit_code = 1)
        else:
            pub.sendMessage('file_quit')
