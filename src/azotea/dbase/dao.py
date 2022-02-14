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

from twisted.logger import Logger
from twisted.enterprise import adbapi


from twisted.internet import reactor, task, defer
from twisted.internet.defer import inlineCallbacks
from twisted.internet.threads import deferToThread

#--------------
# local imports
# -------------

from azotea import SQL_SCHEMA, SQL_INITIAL_DATA_DIR, SQL_UPDATES_DATA_DIR

from azotea.logger import setLogLevel
from azotea.dbase import log, NAMESPACE, tables, image, sky, roi

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

class DataAccesObject():

    def __init__(self, pool, *args, **kargs):
        self.pool = pool
        self.start(*args)
        
       
    #------------
    # Service API
    # ------------

    def start(self, obs_dbg, loc_dbg, cam_dbg, img_dbg, roi_dbg, sky_dbg, cfg_dbg):
        log.debug('Starting DAO')

        self.config = tables.ConfigTable(
            pool      = self.pool,
            log_level = cfg_dbg,
        )
        self.observer = tables.VersionedTable(
            pool                = self.pool, 
            table               = 'observer_t',
            id_column           = 'observer_id',
            natural_key_columns = ('family_name','surname'), 
            other_columns       = ('affiliation','acronym'),
            log_level           = obs_dbg,
        )
        self.location = tables.Table(
            pool                = self.pool, 
            table               = 'location_t',
            id_column           = 'location_id',
            natural_key_columns = ('site_name','location'), 
            other_columns       = ('longitude','latitude','randomized','utc_offset'),
            insert_mode         = tables.QUERY_INSERT_OR_REPLACE,
            log_level           = loc_dbg,
        )
        self.camera = tables.Table(
            pool                = self.pool, 
            table               = 'camera_t',
            id_column           = 'camera_id',
            natural_key_columns = ('model',), 
            other_columns       = ('bias','extension','header_type','bayer_pattern','width','length','x_pixsize','y_pixsize'),
            insert_mode         = tables.QUERY_INSERT_OR_REPLACE,
            log_level           = cam_dbg,
        )
        self.roi = roi.ROITable(
            pool                = self.pool, 
            table               = 'roi_t',
            id_column           = 'roi_id',
            natural_key_columns = ('x1','y1','x2','y2'), 
            other_columns       = ('display_name','comment'),
            insert_mode         = tables.QUERY_INSERT_OR_REPLACE,
            log_level           = roi_dbg,
        )
        self.image = image.ImageTable(
            pool                = self.pool, 
            table               = 'image_t',
            id_column           = 'image_id',
            natural_key_columns = ('name','directory'), 
            other_columns       = ('hash','iso','gain','exptime','focal_length','f_number','session', 'imagetype', 'flagged',
                                   'date_id','time_id','camera_id','observer_id','location_id'),
            insert_mode         = tables.INSERT,
            log_level           = img_dbg,
        )
        self.sky = sky.SkyBrightness(
            pool      = self.pool,
            log_level = sky_dbg,
        )
        