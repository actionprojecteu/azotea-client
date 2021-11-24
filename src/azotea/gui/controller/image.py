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
import sqlite3

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
from azotea.utils.image import hashfunc, exif_metadata, toDateTime, hash_and_exif_metadata
from azotea.logger  import startLogging, setLogLevel
from azotea.error import IncorrectTimestampError
from azotea import FITS_HEADER_TYPE, EXIF_HEADER_TYPE

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
        pub.subscribe(self.onRegisterReq,  'images_register_req')
        pub.subscribe(self.onAbortReq,  'images_abort_load_req')
        pub.subscribe(self.onSetDefaultOpticsReq,  'images_set_default_optics_req')
       

    # --------------
    # Event handlers
    # --------------


    def onAbortReq(self):
        self._abort = True


    @inlineCallbacks
    def onRegisterReq(self):
        try:
            self._abort = False
            ok = yield self.doCheckDefaults()
            if ok:
                images_dir = self.view.openDirectoryDialog()
                if images_dir:
                    with os.scandir(images_dir) as it:
                        dirs  = [ entry.path for entry in it if entry.is_dir()  ]
                        files = [ entry.path for entry in it if entry.is_file() ]
                    N_Files = 0
                    if dirs:
                        if files:
                            log.warn("Ignoring files in {wd}", wd=images_dir)
                        i = 0
                        for images_dir in sorted(dirs, reverse=True):
                            result = yield self.doRegister(images_dir)
                            if not result:
                                break
                            j, M_Files = result
                            i += j
                            N_Files += M_Files
                    else:
                        result = yield self.doRegister(images_dir)
                        if result:
                            i, N_Files = result
                    if N_Files:
                        message = _("Registration: {0}/{1} images complete").format(i,N_Files)
                        self.view.messageBoxInfo(who=_("Register"),message=message)
                    else:
                        extension = '*' + self.extension
                        message = _("No images found with the filter {0}").format(extension)
                        self.view.messageBoxWarn(who=_("Register"),message=message)
                    self.view.statusBar.clear()
        except Exception as e:
            log.failure('{e}',e=e)
            pub.sendMessage('file_quit', exit_code = 1)


    @inlineCallbacks
    def onSetDefaultOpticsReq(self, data):
        try:
            log.info('onSetDefaultOpticsReq() setting & saving default optics {data}', data=data)
            self.default_focal_length = {'focal_length': data['focal_length']}
            self.default_f_number = {'f_number': data['f_number']}
            yield self.model.config.saveSection('optics', data)
        except Exception as e:
            log.failure('{e}',e=e)
            pub.sendMessage('file_quit', exit_code = 1)

    # --------------
    # Helper methods
    # --------------

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
            error_list = '\n'.join(errors)
            message = _("Can't register. These things are missing:\n{0}").format(error_list)
            self.view.messageBoxError(who=_("Register"),message=message)
            return(False)
        else:
            return(True)
    

    @inlineCallbacks
    def saveAndFix(self, save_list):
        try:
            yield self.image.save(save_list)
        except sqlite3.IntegrityError as e:
            for row in save_list:
                try:
                    yield self.image.save(row)
                except  sqlite3.IntegrityError as e:
                    name, directory = yield self.image.getByHash(row)
                    log.warn("Possible duplicate image: '{name}' with existing '{prev}' in {dir}",name=row['name'], prev=name, dir=directory)
                    if row['name'] == name:
                        yield self.image.fixDirectory(row)
                        log.info('Fixed directory for {name} to {dir}', name=row['name'], dir=row['directory'])
                    else:
                        message = _("image: '{0}' is completely discarded, using '{1}' instead").format(row['name'], name)
                        self.view.messageBoxWarn(who=_("Register"), message=message)
                        log.warn("Image: '{name}' is completely discarded, using '{prev}' instead",name=row['name'], prev=name)


    @inlineCallbacks
    def doRegister(self, directory):
        if os.path.basename(directory) == '':
            directory = directory[:-1]
        log.debug('Directory is {dir}.',dir=directory)
        extension = '*' + self.extension
        # AQUI EMPIEZA LO SERIO
        self.view.mainArea.clearImageDataView()
        session = int(datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d%H%M%S'))
        file_list  = sorted(glob.glob(os.path.join(directory, extension)))
        N_Files = len(file_list)
        i = 0
        save_list = list()
        bayer = self.bayer_pattern
        if self.header_type == FITS_HEADER_TYPE:
            message = _("Unsupported header type {0} for the time being").format(header_type)
            self.view.messageBoxError(who=_("Register"),message=message)
            return(None)
        log.debug('Found {n} candidates matching filter {ext}.',n=N_Files, ext=extension)
        for i, filepath in enumerate(file_list, start=1):
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
            row['session'] = session
            if result:
                log.debug('Skipping already registered {row.name}.', row=row)
                self.view.statusBar.update( _("LOADING"), row['name'], (100*i//N_Files))
                continue
            try:
                yield deferToThread(hash_and_exif_metadata, filepath, row)
            except Exception as e:
                log.failure('{e}', e=e)
                message = _("{0}: Error in fingerprint computation or EXIF metadata reading").format(row['name'])
                self.view.statusBar.update( _("LOADING"), row['name'], (100*i//N_Files), error=True)
                return(None)
            new_camera = yield self.model.camera.lookup(row)
            if not new_camera:
                self.view.statusBar.update( _("LOADING"), row['name'], (100*i//N_Files), error=True)
                message = _("Camera model {0} not found in the database").format(row['model'])
                log.warn(message)
                self.view.messageBoxError(who=_("Register"),message=message)
                return(None)
            log.debug('Resolved camera model {row.model} from the data base {info.camera_id}', row=row, info=new_camera)
            row['camera_id'] = int(new_camera['camera_id'])
            self.view.mainArea.displayImageData(row['name'],row)
            self.view.statusBar.update( _("LOADING"), row['name'], (100*i//N_Files))
            save_list.append(row)
            if (i % 50) == 0:
                log.info("Register: saving to database")
                yield self.saveAndFix(save_list)
                save_list = list()
        if save_list:
            log.info("Register: saving to database")
            yield self.saveAndFix(save_list)
        return((i, N_Files))
        