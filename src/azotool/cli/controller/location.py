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

    def __init__(self, model, config):
        self.model  = model
        self.config = config
        setLogLevel(namespace=NAMESPACE, levelStr='info')
        pub.subscribe(self.createReq,  'location_create_req')


    @inlineCallbacks
    def createReq(self, options):
        try:
            site_name  = ' '.join(options.site_name)
            location   = ' '.join(options.location)
            current = {
                'site_name'  : site_name,
                'location'   : location,
                'longitude'  : options.longitude,
                'latitude'   : options.latitude,
                'randomized' : int(options.randomize),
                'utc_offset' : options.utc_offset
            }
            condition  = {'site_name': site_name, 'location': location}
            previous = yield self.model.load(condition)
            if not previous:
                yield self.writeRandomized(current)
            elif previous['randomized'] == 1 and options.randomize:
                previous['utc_offset'] = options.utc_offset
                log.info('Insert to location_t: {data}', data=previous)
                yield self.model.save(previous)
            else:
                yield self.writeRandomized(current)
            if options.default:
                log.debug('Getting id from location_t')
                info_id = yield self.model.lookup(current)
                log.info('Setting default location in configuration section as id = {id}',id=info_id)
                yield self.config.saveSection('location',info_id)
        except Exception as e:
            log.failure('{e}',e=e)
            pub.sendMessage('file_quit', exit_code = 1)
        else:
            pub.sendMessage('file_quit')


    @inlineCallbacks
    def writeRandomized(self, data):
        longitude = data['longitude'] 
        latitude  = data['latitude'] 
        randomizeFlag = data['randomized']
        if longitude and latitude and randomizeFlag:
            long1 = longitude; lat1 = latitude
            longitude, latitude = randomize(longitude, latitude)
            log.info('Randomized coordinates ({long1}, {lat1}) -> ({long2}, {lat2})', 
                long1=long1, lat1=lat1, long2=longitude, lat2=latitude)
        data['longitude'] = longitude
        data['latitude']  = latitude
        log.info('Insert to location_t: {data}', data=data)
        yield self.model.save(data)
