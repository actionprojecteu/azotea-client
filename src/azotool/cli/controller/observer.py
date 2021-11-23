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
        self.default_id = None
        setLogLevel(namespace=NAMESPACE, levelStr='info')
        pub.subscribe(self.createReq,  'observer_create_req')

    @inlineCallbacks
    def createReq(self, options):
        try:
            data = {
                'family_name': ' '.join(options.name),
                'surname'    : ' '.join(options.surname),
                'affiliation': ' '.join(options.affiliation),
                'acronym'    : ' '.join(options.acronym),
            }
            log.info('Versioned insert observer: {data}', data=data)
            yield self.model.save(data)
            if options.default:
                log.debug('Getting id from observer_t')
                info_id = yield self.model.lookup(data)
                log.info('Setting default observer configuration as = {id}',id=info_id)
                yield self.config.saveSection('observer',info_id)
        except Exception as e:
            log.failure('{e}',e=e)
            pub.sendMessage('file_quit', exit_code = 1)
        else:
            pub.sendMessage('file_quit')

    @inlineCallbacks
    def getDefault(self):
        if not self.default_id:
            # loads defaults
            info = yield self.config.load('observer','observer_id')
            self.default_id = info['observer_id']
            if self.default_id:
                self.default_details = yield self.model.loadById(info)
        return((self.default_id,  self.default_details))
