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
from azotea.utils.roi import Rect, reshape_rect

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


class ROIController:

    def __init__(self, model, config):
        self.model = model
        self.config = config
        self.default_id = None
        self.default_details = None
        setLogLevel(namespace=NAMESPACE, levelStr='info')
        pub.subscribe(self.createReq,  'roi_create_req')
        pub.subscribe(self.switchReq,  'roi_switch_req')


    @inlineCallbacks
    def switchReq(self, options):
        try:
            if not options.model:
                raise ValueError("Camera --model option missing")
            data = {
                'model': ' '.join(options.model), 
                'width': options.width, 
                'height': options.height,
            }
            info_id = yield self.model.lookupByComment(data)
            log.info('info_id is = {id}',id=info_id)
            if not info_id:
                raise ValueError("No ROI was found based on comments. Check input parameters")
            log.info('Setting default ROI configuration as = {id}',id=info_id)
            yield self.config.saveSection('ROI',info_id)
        except Exception as e:
            log.failure('{e}',e=e)
            pub.sendMessage('quit', exit_code = 1)
        else:
            pub.sendMessage('quit')


    @inlineCallbacks
    def createReq(self, options):
        try:
            if options.as_given:
                data = self.createAsGiven(options)
            else:
                data = yield self.createByImage(options.from_image, options.width, options.height)
            log.info('Insert/replace ROI: {data}', data=data)
            yield self.model.save(data)
            if options.default:
                log.debug('Getting id from roi_t')
                info_id = yield self.model.lookup(data)
                log.info('Setting default ROI configuration as = {id}',id=info_id)
                yield self.config.saveSection('ROI',info_id)
        except Exception as e:
            log.failure('{e}',e=e)
            pub.sendMessage('quit', exit_code = 1)
        else:
            pub.sendMessage('quit')


    @inlineCallbacks
    def getDefault(self):
        if not self.default_id:
            # loads defaults
            info = yield self.config.load('ROI','roi_id')
            self.default_id = info['roi_id']
            if self.default_id:
                self.default_details = yield self.model.loadById(info)
        return((self.default_id,  self.default_details))


    def createAsGiven(self, options):
        x1 = options.x1; y1 = options.y1
        x2 = options.x2; y2 = options.y2
        comment = options.comment
        if x1 and y1 and x2 and y2:
            rect = Rect(x1=x1, y1=y1, x2=x2, y2=y2)
            return {
                'x1': x1,
                'y1': y1,
                'x2': x2,
                'y2': y2,
                'comment': ' '.join(comment) if comment else None,
                'display_name': str(rect),
            }
        else:
            raise ValueError("One or more coordinates is missing (x1,y1,x2,y2)")

    @inlineCallbacks
    def createByImage(self, path, width, height):
        if width and height:
            rect = Rect(x1=0, y1=0, x2=width, y2=height)
            info = yield deferToThread(reshape_rect, path, rect)
            return(info)
        else:
            raise ValueError("width or height is missing")

        
