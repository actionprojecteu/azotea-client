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
from twisted.internet.threads import deferToThread

# -------------------
# Third party imports
# -------------------

from pubsub import pub

#--------------
# local imports
# -------------

from azotea.logger  import setLogLevel
from azotool.cli   import NAMESPACE, log
from azotea.utils.camera import image_analyze


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

class CameraController:

    def __init__(self, model, config):
        self.model  = model
        self.config = config
        setLogLevel(namespace=NAMESPACE, levelStr='info')
        pub.subscribe(self.createReq,  'camera_create_req')

    @inlineCallbacks
    def createReq(self, options):
        try:
            if options.as_given:
                data = self.createAsGiven(options)
            else:
                data = yield self.createByImage(options.from_image)
            log.info('Insert/replace camera data: {data}', data=data)
            yield self.model.save(data)
            if options.default:
                log.debug('Getting id from camera_t')
                info_id = yield self.model.lookup(data)
                log.info('Setting default camera configuration as = {id}',id=info_id)
                yield self.config.saveSection('camera',info_id)
        except Exception as e:
            log.failure('{e}',e=e)
            pub.sendMessage('quit', exit_code = 1)
        else:
            pub.sendMessage('quit')


    @inlineCallbacks
    def createByImage(self, path):
        if not path:
            raise ValueError("--from-image path is missing")
        info, warning = yield deferToThread(image_analyze, path)
        if not info:
            raise ValueError(warning)
        log.info("Analyzed EXIF from image is {info}", info=info)
        old_info = yield self.model.load(info)    # lookup by model
        if not old_info:
            log.warn("Camera is not yet in the database")
        if warning:
            log.warn("{message}", message=warning)
        return(info)


    def createAsGiven(self, options):
        if not options.model:
            raise ValueError("--model is missing")
        if not options.extension:
            raise ValueError("--extension is missing")
        if not options.bias:
            raise ValueError("--bias is missing")
        return {
            'model'        : ' '.join(options.model),
            'bias'         : options.bias,
            'extension'    : options.extension,
            'header_type'  : options.header_type,
            'bayer_pattern': options.bayer_pattern,
            'width'        : options.width,
            'length'       : options.length,
        }
        
