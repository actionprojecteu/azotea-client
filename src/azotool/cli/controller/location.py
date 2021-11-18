# ----------------------------------------------------------------------
# Copyright (c) 2020
#
# See the LICENSE file for details
# see the AUTHORS file for authors
# ----------------------------------------------------------------------

#--------------------
# System wide imports
# -------------------

import math
import random 

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

def randomize(longitude, latitude):
        
    log.info('Randomizing public coordinates')
    # Includes +- 1Km uncertainty in coordinates
    delta_long  = random.uniform(-1,1)*(1/6371)*math.cos(math.radians(latitude))
    delta_lat   = random.uniform(-1,1)*(1/6371)
    random_long = longitude + math.degrees(delta_long)
    random_lat  = latitude  + math.degrees(delta_lat)
    return random_long, random_lat


# --------------
# Module Classes
# --------------

class LocationController:

    def __init__(self, parent, model, config):
        self.parent = parent
        self.model  = model
        self.config = config
        self.default_id = None
        self.default_details = None
        setLogLevel(namespace=NAMESPACE, levelStr='info')
        pub.subscribe(self.createReq,  'location_create_req')

    def start(self):
        log.info('starting Location Controller')

    @inlineCallbacks
    def createReq(self, options):
        if options.longitude and options.latitude:
            random_long, random_lat = randomize(options.longitude, options.latitude)
        else:
            random_long, random_lat = (None, None)

        data = {
            'site_name'  : ' '.join(options.site_name),
            'location'   : ' '.join(options.location),
            'longitude'  : options.longitude,
            'latitude'   : options.latitude,
            'public_long': random_long,
            'public_lat' : random_lat,
            'utc_offset' : options.utc_offset
        }
        try:
            log.info('Insert to location_t: {data}', data=data)
            yield self.model.save(data)
            log.debug('Getting id from location_t')
            info_id = yield self.model.lookup(data)
            log.info('Setting default location in configuration section as id = {id}',id=info_id)
            yield self.config.saveSection('location',info_id)
        except Exception as e:
            log.failure('{e}',e=e)
            pub.sendMessage('file_quit', exit_code = 1)
        else:
            pub.sendMessage('file_quit')
