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
import glob
import hashlib
import gettext
import datetime

from fractions import Fraction
from sqlite3 import IntegrityError

# ---------------
# Twisted imports
# ---------------

from twisted.logger   import Logger
from twisted.internet import  reactor, defer
from twisted.internet.defer import inlineCallbacks
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
from tkazotea.error import IncorrectTimestampError
from tkazotea.gui import FITS_HEADER_TYPE, EXIF_HEADER_TYPE

# ----------------
# Module constants
# ----------------

NAMESPACE = 'CTRL '
DEF_TSTAMP = '%Y-%m-%dT%H:%M:%S'

# -----------------------
# Module global variables
# -----------------------

# Support for internationalization
_ = gettext.gettext

log = Logger(namespace=NAMESPACE)

# ------------------------
# Module Utility Functions
# ------------------------

def hash(filepath):
    '''Compute a hash from the image'''
    BLOCK_SIZE = 1048576 # 1MByte, the size of each read from the file
    # md5() was the fastest algorithm I've tried    
    file_hash = hashlib.md5()
    with open(filepath, 'rb') as f:
        block = f.read(BLOCK_SIZE) 
        while len(block) > 0:
            file_hash.update(block)
            block = f.read(BLOCK_SIZE)
    return file_hash.digest()


def exif_metadata(filename, row):
    
    with open(filename, 'rb') as f:
        exif = exifread.process_file(f, details=False)
    if not exif:
        log.warn('Could not open EXIF metadata from {file}',file=filename)
        return row
    row['model']        = str(exif.get('Image Model', None)).strip()
    row['iso']          = str(exif.get('EXIF ISOSpeedRatings', None))
    row['focal_length'] = float(Fraction(str(exif.get('EXIF FocalLength', 0))))
    row['f_number']     = float(Fraction(str(exif.get('EXIF FNumber', 0))))
    row['exptime']      = float(Fraction(str(exif.get('EXIF ExposureTime', 0))))
    row['date_id'], row['time_id'], row['widget_date'], row['widget_time'] = toDateTime(str(exif.get('Image DateTime', None)))
   
    # Fixes missing Focal Length and F/ ratio
    row['focal_length'] = row['def_fl'] if row['focal_length'] == 0 else row['focal_length']
    row['f_number']     = row['def_fn'] if row['f_number']     == 0 else row['f_number']

    # Fixed GAIN for EXIF DSLRs that provide ISO sensivity
    row['gain'] = None
    return row


def toDateTime(tstamp):
    tstamp_obj = None
    for fmt in ['%Y:%m:%d %H:%M:%S',]:
        try:
            tstamp_obj = datetime.datetime.strptime(tstamp, fmt)
        except ValueError:
            continue
        else:
            break
    if not tstamp_obj:
        raise IncorrectTimestampError(tstamp)
    else:
        date_id = int(tstamp_obj.strftime('%Y%m%d'))
        time_id = int(tstamp_obj.strftime('%H%M%S'))
        widged_date = tstamp_obj.strftime('%Y-%m-%d')
        widget_time = tstamp_obj.strftime('%H:%M:%S')
        return date_id, time_id, widged_date, widget_time


def expensiveEXIFOperation(filepath, row):
    log.debug('Computing {row.name} MD5 hash', row=row)
    row['hash'] = hash(filepath)
    log.debug('Loading {row.name} EXIF metadata', row=row)
    row = exif_metadata(filepath, row)


# --------------
# Module Classes
# --------------

class ImageController:

    NAME = NAMESPACE

    def __init__(self, parent, view, model):
        self.parent = parent
        self.model = model
        self.image = model.image
        self.config = model.config
        self.view = view
        self.default_focal_length = None
        self.default_f_number = None
        self._abort = False
        setLogLevel(namespace=NAMESPACE, levelStr='info')
           
    def start(self):
        log.info('starting Register Controller')
        pub.subscribe(self.begin,  'images_load_req')
        pub.subscribe(self.abort,  'images_abort_load_req')
        pub.subscribe(self.onSetDefaultOpticsReq,  'images_set_default_optics_req')

    def abort(self):
        self._abort = True
 
    # -----------------------
    # Subscriptions from View
    # -----------------------

    @inlineCallbacks
    def begin(self):
        self._abort = False
        ok = yield self.doCheckDefaults()
        if ok:
            work_dir = self.view.openDirectoryDialog()
            if work_dir:
                with os.scandir(work_dir) as it:
                    dirs  = [ entry.path for entry in it if entry.is_dir()  ]
                    files = [ entry.path for entry in it if entry.is_file() ]
                if dirs:
                    if files:
                        log.warn("Ignoring files in {wd}", wd=work_dir)
                    i = 0; N_Files = 0
                    for work_dir in sorted(dirs, reverse=True):
                        result = yield self.doRegister(work_dir)
                        if not result:
                            break
                        j, M_Files = result
                        i += j
                        N_Files += M_Files
                else:
                    result = yield self.doRegister(work_dir)
                    if result:
                        i, N_Files = result
                
                if N_Files:
                    message = _("Registration: {0}/{1} images complete").format(i,N_Files)
                    self.view.messageBoxInfo(who=_("Register"),message=message)
                else:
                    extension = '*' + self.extension
                    message = _("No images found with the filter {0}").format(extension)
                    pub.sendMessage('view_messageBoxWarn',who=_("Register"),message=message)
                self.view.statusBar.clear()


    # We assign the default optics here
    @inlineCallbacks
    def getDefault(self):
        if not self.default_focal_length:
            self.default_focal_length = yield self.config.load('optics','focal_length')
        if not self.default_f_number:
            self.default_f_number = yield self.config.load('optics','f_number')
        return((self.default_focal_length,  self.default_f_number))


    @inlineCallbacks
    def onSetDefaultOpticsReq(self, data):
        try:
            log.info('onSetDefaultOpticsReq() setting & saving default optics {data}', data=data)
            self.default_focal_length = {'focal_length': data['focal_length']}
            self.default_f_number = {'f_number': data['f_number']}
            yield self.model.config.saveSection('optics', data)
        except Exception as e:
            log.failure('{e}',e=e)
         

    @inlineCallbacks
    def doCheckDefaults(self):
        errors = list()
        log.debug('doCheckDefaults()')
        default_camera_id,   default_camera   = yield self.cameraCtrl.getDefault()
        default_observer_id, default_observer = yield self.observerCtrl.getDefault()
        default_location_id, default_location = yield self.locationCtrl.getDefault()
     
        if default_camera_id:
            self.camera_id = int(default_camera_id)
            self.extension     = default_camera['extension']
            self.header_type   = default_camera['header_type']
            self.bayer_pattern = default_camera['bayer_pattern']
            self.global_bias   = default_camera['bias']
        else:
            self.camera_id = None
            errors.append( _("- No default camera selected.") )

        if not self.default_focal_length:
            errors.append( _("- No default focal length defined.") )

        if not self.default_f_number:
            errors.append( _("- No default f/ number defined.") )

        if default_observer_id:
            self.observer_id = int(default_observer_id)
        else:
            self.observer_id = None
            errors.append( _("- No default observer defined.") )

        if default_location_id:
            self.location_id = int(default_location_id)
        else:
            self.location_id = None
            errors.append( _("- No default location defined.") )

        if errors:
            error_list = '\n'.join(errors)
            message = _("Can't register. These things are missing:\n{0}").format(error_list)
            pub.sendMessage('view_messageBoxError',who=_("Register"),message=message)
            return(False)
        else:
            return(True)
    

    # ---------------------- OBSERVER ----------------------------------------------


    @inlineCallbacks
    def doRegister(self, directory):
        if os.path.basename(directory) == '':
            directory = directory[:-1]
        log.debug('Directory is {dir}.',dir=directory)
        extension = '*' + self.extension
        # AQUI EMPIEZA LO SERIO
        self.view.mainArea.clearImageDataView()
        session = int(datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S'))
        file_list  = sorted(glob.glob(os.path.join(directory, extension)))
        N_Files = len(file_list)
        i = 0
        bayer = self.bayer_pattern
        log.debug('Found {n} candidates matching filter {ext}.',n=N_Files, ext=extension)
        for i, filepath in enumerate(file_list):
            if self._abort:
                break
            row = {
                'name'        : os.path.basename(filepath), 
                'directory'   : os.path.dirname(filepath),
                'header_type' : self.header_type,
                'observer_id' : self.observer_id,
                'location_id' : self.location_id,
                'def_fl'      : self.default_focal_length['focal_length'],  # these 2 are not real table columns
                'def_fn'      : self.default_f_number['f_number'],      # they are here just to fix EXIF optics reading
            }
            result = yield self.image.load(row)
            if result:
                log.debug('Skipping already registered {row.name}.', row=row)
                self.view.statusBar.update( _("LOADING"), row['name'], (100*i//N_Files))
                continue
            row['session'] = session
            if row['header_type'] == FITS_HEADER_TYPE:
                message = _("Unsupported header type {0} for the time being").format(header_type)
                pub.sendMessage('view_messageBoxError',who=_("Register"),message=message)
                return(None)
            else:
                try:
                    yield deferToThread(expensiveEXIFOperation, filepath, row)
                except Exception as e:
                    log.failure('{e}', e=e)
                    message = _("{0}: Error in MD5 computation or EXIF metadata reading").format(row['name'])
                    self.view.statusBar.update( _("LOADING"), row['name'], (100*i//N_Files), error=True)
                    return(None)
            new_camera = yield self.model.camera.lookup(row)
            if not new_camera:
                self.view.statusBar.update( _("LOADING"), row['name'], (100*i//N_Files), error=True)
                message = _("Camera model {0} not found in the database").format(row['model'])
                log.warn(message)
                pub.sendMessage('view_messageBoxError',who=_("Register"),message=message)
                return(None)
            log.debug('Resolved camera model {row.model} from the data base {info.camera_id}', row=row, info=new_camera)
            row['camera_id'] = int(new_camera['camera_id'])
            try:
                yield self.image.save(row)
                self.view.mainArea.displayImageData(row['name'],row)
            except IntegrityError as e:
                #log.warn('Image with the same MD5 hash in the data base for {row}', row=row)
                yield self.image.fixDirectory(row)
                self.view.statusBar.update( _("LOADING"), row['name'], (100*i//N_Files))
                log.debug('Fixed directory for {name}', name=row['name'])
                continue
            else:
                self.view.statusBar.update( _("LOADING"), row['name'], (100*i//N_Files))
        return((i+1, N_Files))
        