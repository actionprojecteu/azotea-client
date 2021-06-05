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
import gettext

# ---------------
# Twisted imports
# ---------------

from twisted.logger   import Logger
from twisted.internet import  reactor, defer
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.internet.threads import deferToThread

# -------------------
# Third party imports
# -------------------

from pubsub import pub
import exifread
import rawpy

#--------------
# local imports
# -------------

from tkazotea import __version__
from tkazotea.utils import Point, Rect
from tkazotea.logger  import startLogging, setLogLevel
from tkazotea.error import TooDifferentValuesBiasError, NotPowerOfTwoErrorBiasError, UnsupportedCFAError

# ----------------
# Module constants
# ----------------

# Support for internationalization
_ = gettext.gettext

NAMESPACE = 'CTRL '

BAYER_LETTER = ['B','G','R','G']

# -----------------------
# Module global variables
# -----------------------

log = Logger(namespace=NAMESPACE)

# ------------------------
# Module Utility Functions
# ------------------------

def nearest_power_of_two(bias):
    if bias == 0:
        return 0, False
    warning = False
    N1 = math.log10(bias)/math.log10(2)
    N2 = int(round(N1,0))
    log.debug("N1 = {n1}, N2 = {n2}",n1=N1, n2=N2)
    nearest = 2**N2
    if (math.fabs(N1-N2) > 0.012):  # determinend empirically for bias=127
        warning = True
    return nearest, warning


def analyze_bias(levels):
    log.info("analyzing bias levels({levels})",levels=levels)
    global_bias = min(levels)
    if max(levels) - global_bias > 4:
        raise TooDifferentValuesBiasError(global_bias, levels, 4)
    tuples   = [nearest_power_of_two(bias) for bias in levels]
    log.info("biases tuples = {tuples}",tuples=tuples)
    biases   = [item[0] for item in tuples]
    warnings = [item[1] for item in tuples]
    if any(warnings):
        raise NotPowerOfTwoErrorBiasError(global_bias, levels)
    global_bias = biases[0]
    return global_bias
      


def image_analyze_exif(filename):
    extension = os.path.splitext(filename)[1]
    result = None
    with open(filename, 'rb') as f:
        exif = exifread.process_file(f, details=False)
    if not exif:
        log.warn('Could not open EXIF metadata from {file}',file=filename)
        return None
    model = str(exif.get('Image Model', None)).strip()
    warning = False
    with rawpy.imread(filename) as img:
        color_desc = img.color_desc.decode('utf-8')
        if color_desc != 'RGBG':
            raise UnsupporteCFAError(color_desc)
        bayer_pattern = ''.join([ BAYER_LETTER[img.raw_pattern[row,column]] for row in (1,0) for column in (1,0)])
        length, width = img.raw_image.shape    # Raw numbers, not divide by 2
        levels = img.black_level_per_channel
    try:
        bias = analyze_bias(levels)
    except NotPowerOfTwoErrorBiasError as e:
        bias = e.bias
        warning = str(e)
    except TooDifferentValuesBiasError as e:
        bias = e.bias
        warning = str(e)
    else:
        warning = None
    info = {
        'model'         : model,
        'extension'     : extension,
        'bias'          : bias,
        'width'         : width,
        'length'        : length,
        'header_type'   : 'EXIF',
        'bayer_pattern' : bayer_pattern,
    }
    log.debug("CAMERA SUMMARY INFO = {i}",i=info)
    return info, warning


# --------------
# Module Classes
# --------------

class CameraController:

    def __init__(self, parent, view, model, config):
        self.parent = parent
        self.model = model
        self.config = config
        self.view = view
        self.default_id = None
        self.default_details = None
        setLogLevel(namespace=NAMESPACE, levelStr='info')
       
    def start(self):
        log.info('starting Camera Controller')
        pub.subscribe(self.onListReq,        'camera_list_req')
        pub.subscribe(self.onDetailsReq,     'camera_details_req')
        pub.subscribe(self.onSaveReq,        'camera_save_req')
        pub.subscribe(self.onSetDefaultReq,  'camera_set_default_req')
        pub.subscribe(self.onDeleteReq,      'camera_delete_req')
        pub.subscribe(self.onChooseImageReq, 'camera_choose_image_req')
        

    @inlineCallbacks
    def getDefault(self):
        if not self.default_id:
            # loads defaults
            info = yield self.config.load('camera','camera_id')
            self.default_id = info['camera_id']
            if self.default_id:
                self.default_details = yield self.model.loadById(info)
                log.debug("getDefault() CAMERA LOADED DETAILS {d}",d=self.default_details)
        returnValue((self.default_id,  self.default_details))
       


    @inlineCallbacks
    def onChooseImageReq(self, path):
        info, warning = yield deferToThread(image_analyze_exif, path)
        old_info = yield self.model.load(info)    # lookup by model
        if not old_info:
            message = _("Camera not in database!")
            self.view.messageBoxWarn('Preferences',message)
        self.view.menuBar.preferences.cameraFrame.updateCameraInfoFromImage(info)
        if warning:
            self.view.messageBoxWarn('Preferences', warning)

    @inlineCallbacks
    def onListReq(self):
        try:
            log.debug('onListReq() fetching all unique entries from camera_t')
            info = yield self.model.loadAllNK()
            self.view.mainArea.cameraCombo.fill(info)
            preferences = self.view.menuBar.preferences
            if preferences:
                preferences.cameraFrame.listResp(info)
            # Also loads default camera
            if self.default_details:
                self.view.mainArea.cameraCombo.set(self.default_details)
                if preferences:
                    preferences.cameraFrame.detailsResp(self.default_details)
        except Exception as e:
            log.failure('{e}',e=e)


    @inlineCallbacks
    def onDetailsReq(self, data):
        try:
            log.info('getCamerasDetails() fetching details from camera_t given by {data}', data=data)
            info = yield self.model.load(data)
            log.info('getCamerasDetails() fetched details from camera_t returns {info}', info=info)
            self.view.menuBar.preferences.cameraFrame.detailsResp(info)
        except Exception as e:
            log.failure('{e}',e=e)


    @inlineCallbacks
    def onSaveReq(self, data):
        try:
            log.info('onSaveReq() insert/replace {data} details from camera_t', data=data)
            yield self.model.save(data)
            log.info('onSaveReq() insert/replace ok from camera_t')
            self.view.menuBar.preferences.cameraFrame.saveOkResp()
        except Exception as e:
            log.failure('{e}',e=e)


    @inlineCallbacks
    def onSetDefaultReq(self, data):
        try:
            log.info('onSetDefaultReq() geting id from camera_t given by {data}', data=data)
            info_id = yield self.model.lookup(data)
            self.default_id = info_id['camera_id']
            self.default_details = yield self.model.loadById(info_id)
            log.info('onSetDefaultReq() returned id from camera_t is {id}',id=info_id)
            log.info('onSetDefaultReq() returned details from camera_t is {d}',d=self.default_details)
            yield self.config.saveSection('camera',info_id)
            pub.sendMessage('camera_list_req')  # send a message to itself to update the views
        except Exception as e:
            log.failure('{e}',e=e)


    @inlineCallbacks
    def onDeleteReq(self, data):
        try:
            log.info('onDeleteReq() deleting entry from camera_t given by {data}', data=data)
            count = yield self.model.delete(data)
        except Exception as e:
            log.failure('{e}',e=e)
            self.view.menuBar.preferences.cameraFrame.deleteErrorResponse(count)
        yield self.onListReq()
        self.view.menuBar.preferences.cameraFrame.deleteOkResponse(count)

