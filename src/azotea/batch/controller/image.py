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

from azotea import __version__
from azotea.utils.roi import Point, Rect
from azotea.utils.image import hashfunc, exif_metadata, toDateTime, expensiveEXIFOperation
from azotea.logger  import startLogging, setLogLevel
from azotea.error import IncorrectTimestampError
from azotea.gui import FITS_HEADER_TYPE, EXIF_HEADER_TYPE

# ----------------
# Module constants
# ----------------

NAMESPACE = 'CTRL '

# -----------------------
# Module global variables
# -----------------------

# Support for internationalization
_ = gettext.gettext

log = Logger(namespace=NAMESPACE)

# ------------------------
# Module Utility Functions
# ------------------------




# --------------
# Module Classes
# --------------

class ImageController:

    NAME = NAMESPACE

    def __init__(self, parent, model, work_dir):
        self.parent = parent
        self.model = model
        self.image = model.image
        self.config = model.config
        self.default_focal_length = None
        self.default_f_number = None
        self._abort = False
        self.work_dir = work_dir
        setLogLevel(namespace=NAMESPACE, levelStr='info')
         

    @inlineCallbacks  
    def start(self):
        log.info('Starting Register Controller')
        self._abort = False
        ok = yield self.doCheckDefaults()
        if not ok:
            log.error("Missing default values")
            self.parent.quit()
            return

        work_dir = self.work_dir

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
            self.log.info("Register: {i}/{N} images complete", i=i, N=N_Files)
        else:
            extension = '*' + self.extension
            self.log.warn("Register: No images found with the filter {ext}",ext=extension)
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
            for err in errors:
                log.error("Register: Error {err}", err=err)
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
                log.info("Register: Loading {n} [{p}%]", n=row['name'], p=(100*i//N_Files) )
                continue
            row['session'] = session
            if row['header_type'] == FITS_HEADER_TYPE:
                message = _("Unsupported header type {0} for the time being").format(header_type)
                log.error("Register: Unsupported header type {h} for the time being",h=header_type) 
                return(None)
            else:
                try:
                    yield deferToThread(expensiveEXIFOperation, filepath, row)
                except Exception as e:
                    log.failure('{e}', e=e)
                    log.error("Register: Error in MD5 computation or EXIF metadata reading on {n} [{p}%]",
                        n=row['name'], p=(100*i//N_Files))
                    return(None)
            new_camera = yield self.model.camera.lookup(row)
            if not new_camera:
                log.info("Register: Loading {n} [{p}%]", n=row['name'], p=(100*i//N_Files) )
                log.error("Register: Camera model {m} not found in the database",m=row['model'])
                return(None)
            log.debug('Resolved camera model {row.model} from the data base {info.camera_id}', row=row, info=new_camera)
            row['camera_id'] = int(new_camera['camera_id'])
            try:
                yield self.image.save(row)
                #self.view.mainArea.displayImageData(row['name'],row)
            except IntegrityError as e:
                #log.warn('Image with the same MD5 hash in the data base for {row}', row=row)
                yield self.image.fixDirectory(row)
                log.debug('Fixed directory for {name}', name=row['name'])
                log.info("Register: Loading {n} [{p}%]", n=row['name'], p=(100*i//N_Files) )
                continue
            else:
                log.info("Register: Loading {n} [{p}%]", n=row['name'], p=(100*i//N_Files) )
        return((i+1, N_Files))
        