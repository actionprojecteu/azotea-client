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
import glob
import datetime
import sqlite3

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

from azotea import FITS_HEADER_TYPE, EXIF_HEADER_TYPE
from azotea.logger  import setLogLevel
from azotea.utils.image import hashfunc, exif_metadata, toDateTime, hash_and_exif_metadata
from azotea.batch.controller import NAMESPACE, log


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

class ImageController:

    NAME = NAMESPACE

    def __init__(self, model, config, images_dir):
        self.model = model
        self.image = model.image
        self.config = config
        self.default_focal_length = None
        self.default_f_number = None
        self.images_dir = images_dir
        setLogLevel(namespace=NAMESPACE, levelStr='info')
        pub.subscribe(self.onRegisterReq, 'images_register_req')
         

    # --------------
    # Event handlers
    # --------------

    @inlineCallbacks  
    def onRegisterReq(self):
        try:
            log.info('Starting Register Controller')
            ok = yield self.doCheckDefaults()
            if not ok:
                log.error("Missing default values")
                pub.sendMessage('file_quit', exit_code = 1)
                return
            images_dir = self.images_dir
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
                log.info("Register: {i}/{N} images complete", i=i, N=N_Files)
            else:
                extension = '*' + self.extension
                log.warn("Register: No images found with the filter {ext}",ext=extension)
        except Exception as e:
            log.failure('{e}',e=e)
            pub.sendMessage('file_quit', exit_code = 1)
        else:
            pub.sendMessage("sky_brightness_stats_req")

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
        default_focal_length, default_f_number= yield self.getDefault()
     
        if default_camera_id:
            self.camera_id     = int(default_camera_id)
            self.extension     = default_camera['extension']
            self.header_type   = default_camera['header_type']
            self.bayer_pattern = default_camera['bayer_pattern']
            self.global_bias   = default_camera['bias']
        else:
            self.camera_id = None
            errors.append( "- No default camera selected.")

        if not self.default_focal_length:
            errors.append( "- No default focal length defined.")

        if not self.default_f_number:
            errors.append( "- No default f/ number defined.")

        if default_observer_id:
            self.observer_id = int(default_observer_id)
        else:
            self.observer_id = None
            errors.append( "- No default observer defined.")

        if default_location_id:
            self.location_id = int(default_location_id)
        else:
            self.location_id = None
            errors.append( "- No default location defined.") 

        if errors:
            for err in errors:
                log.error("Register: Error {err}", err=err)
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
                        log.warn("Image: '{name}' is completely discarded, using '{prev}' instead",name=row['name'], prev=name)


    @inlineCallbacks
    def doRegister(self, directory):
        if os.path.basename(directory) == '':
            directory = directory[:-1]
        log.debug('Directory is {dir}.',dir=directory)
        extension = '*' + self.extension
        # AQUI EMPIEZA LO SERIO
        session = int(datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d%H%M%S'))
        file_list  = sorted(glob.glob(os.path.join(directory, extension)))
        N_Files = len(file_list)
        bayer = self.bayer_pattern
        log.info('Found {n} candidates matching filter {ext} in directory {dir}.',n=N_Files, ext=extension, dir=directory)
        if self.header_type == FITS_HEADER_TYPE:
            log.error("Register: Unsupported header type {h} for the time being",h=header_type) 
            return(None)
        i = 0
        save_list = list()
        for i, filepath in enumerate(file_list, start=1):
            row = {
                'name'        : os.path.basename(filepath), 
                'directory'   : os.path.dirname(filepath),
                'header_type' : self.header_type,
                'observer_id' : self.observer_id,
                'location_id' : self.location_id,
                'def_fl'      : self.default_focal_length['focal_length'],  # these 2 are not real table columns
                'def_fn'      : self.default_f_number['f_number'],      # they are here just to fix EXIF optics reading
            }
            log.info("Register: Loading {n} ({i}/{N}) [{p}%]", i=i, N=N_Files, n=row['name'], p=(100*i//N_Files) )
            result = yield self.image.load(row)
            row['session'] = session
            if result:
                log.debug('Skipping already registered {row.name}.', row=row)
                continue
            try:
                yield deferToThread(hash_and_exif_metadata, filepath, row)
            except Exception as e:
                log.failure('{e}', e=e)
                log.error("Register: Error in fingerprint computation or EXIF metadata reading on {n} ({i}/{N}) [{p}%]",
                        i=i, N=N_Files, n=row['name'], p=(100*i//N_Files))
                return(None)
            new_camera = yield self.model.camera.lookup(row)
            if not new_camera:
                log.error("Register: Camera model {m} not found in the database",m=row['model'])
                return(None)
            log.debug('Resolved camera model {row.model} from the data base {info.camera_id}', row=row, info=new_camera)
            row['camera_id'] = int(new_camera['camera_id'])
            save_list.append(row)
            if (i % 50) == 0:
                log.info("Register: saving to database")
                yield self.saveAndFix(save_list)
                save_list = list()
        if save_list:
            log.info("Register: saving to database")
            yield self.saveAndFix(save_list)
        return((i, N_Files))
        