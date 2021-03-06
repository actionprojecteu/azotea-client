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
import uuid
import sqlite3
import glob


# ---------------
# Twisted imports
# ---------------

from twisted.application.service import Service
from twisted.logger import Logger
from twisted.enterprise import adbapi


from twisted.internet import reactor, task, defer
from twisted.internet.defer import inlineCallbacks
from twisted.internet.threads import deferToThread

# -------------------
# Third party imports
# -------------------

from pubsub import pub

#--------------
# local imports
# -------------

from azotea import SQL_SCHEMA, SQL_INITIAL_DATA_DIR, SQL_UPDATES_DATA_DIR

from azotea.utils import set_status_code
from azotea.utils.database import create_database, create_schema
from azotea.logger import setLogLevel
from azotea.dbase.dao import DataAccesObject
from azotea.dbase import NAMESPACE, log 

# ----------------
# Module constants
# ----------------

SQL_TEST_STRING = "SELECT COUNT(*) FROM image_t"

# -----------------------
# Module global variables
# -----------------------

# ------------------------
# Module Utility Functions
# ------------------------

def getPool(*args, **kargs):
    '''Get connetion pool for sqlite3 driver'''
    kargs['check_same_thread'] = False
    return adbapi.ConnectionPool("sqlite3", *args, **kargs)


def read_database_version(connection):
    cursor = connection.cursor()
    query = 'SELECT value FROM config_t WHERE section = "database" AND property = "version";'
    cursor.execute(query)
    version = cursor.fetchone()[0]
    return version


def write_database_uuid(connection):
    guid = str(uuid.uuid4())
    cursor = connection.cursor()
    param = {'section': 'database','property':'uuid','value': guid}
    cursor.execute(
        '''
        INSERT INTO config_t(section,property,value) 
        VALUES(:section,:property,:value)
        ''',
        param
    )
    connection.commit()
    return guid


def make_database_uuid(connection):
    cursor = connection.cursor()
    query = 'SELECT value FROM config_t WHERE section = "database" AND property = "uuid";'
    cursor.execute(query)
    guid = cursor.fetchone()
    if guid:
        try:
            uuid.UUID(guid[0])  # Validate UUID
        except ValueError:
            guid = write_database_uuid(connection)
        else:
            guid = guid[0]
    else:
        guid = write_database_uuid(connection)
    return guid


def read_debug_levels(connection):
    cursor = connection.cursor()
    query = 'SELECT value FROM config_t WHERE section = "tables" AND property = "observer_t";'
    cursor.execute(query)
    observer = cursor.fetchone()[0]
    cursor = connection.cursor()
    query = 'SELECT value FROM config_t WHERE section = "tables" AND property = "location_t";'
    cursor.execute(query)
    location = cursor.fetchone()[0]
    cursor = connection.cursor()
    query = 'SELECT value FROM config_t WHERE section = "tables" AND property = "camera_t";'
    cursor.execute(query)
    camera = cursor.fetchone()[0]
    cursor = connection.cursor()
    query = 'SELECT value FROM config_t WHERE section = "tables" AND property = "image_t";'
    cursor.execute(query)
    image = cursor.fetchone()[0]
    cursor = connection.cursor()
    query = 'SELECT value FROM config_t WHERE section = "tables" AND property = "roi_t";'
    cursor.execute(query)
    roi = cursor.fetchone()[0]
    cursor = connection.cursor()
    query = 'SELECT value FROM config_t WHERE section = "tables" AND property = "sky_brightness_t";'
    cursor.execute(query)
    sky = cursor.fetchone()[0]
    query = 'SELECT value FROM config_t WHERE section = "tables" AND property = "config_t";'
    cursor.execute(query)
    config = cursor.fetchone()[0]
    result = (observer, location, camera, image, roi, sky, config)
    return result




# --------------
# Module Classes
# --------------

class DatabaseService(Service):

    # Service name
    NAME = NAMESPACE

    def __init__(self, path, create_only, **kargs):
        super().__init__()   
        self.path = path
        self.pool = None
        self.preferences = None
        self.getPoolFunc = getPool
        self.create_only = create_only
    
    def foreign_keys(self, flag):
        def _foreign_keys(txn, flag):
            value = "ON" if flag else "OFF"
            sql = f"PRAGMA foreign_keys={value};"
            txn.execute(sql)
        return self.pool.runInteraction(_foreign_keys, flag)

    #------------
    # Service API
    # ------------

    def startService(self):
        setLogLevel(namespace=NAMESPACE, levelStr='warn')
        connection, new_database = create_database(self.path)
        if new_database:
            log.warn("Created new database file at {f}",f=self.path)
        just_created, file_list = create_schema(connection, SQL_SCHEMA, SQL_INITIAL_DATA_DIR, SQL_UPDATES_DATA_DIR, SQL_TEST_STRING)
        if just_created:
            for sql_file in file_list:
                log.warn("Populating data model from {f}", f=os.path.basename(sql_file))
        else:
            for sql_file in file_list:
                log.warn("Applying updates to data model from {f}", f=os.path.basename(sql_file))
        levels  = read_debug_levels(connection)
        version = read_database_version(connection)
        guid    = make_database_uuid(connection)
        log.warn("Starting {service} on {database}, version = {version}, UUID = {uuid}", 
            database = self.path, 
            version  = version,
            service  = self.name,
            uuid     = guid,
        )
        pub.subscribe(self.quit,  'quit')
        # Remainder Service initialization
        super().startService()
        connection.commit()
        connection.close()
        if self.create_only:
            self.quit(exit_code=0)
        else:
            self.openPool()
            self.dao = DataAccesObject(self.pool, *levels)
            self.dao.version = version
            self.dao.uuid = guid
            self.foreign_keys(True)


    def stopService(self):
        log.info("Stopping Database Service")
        self.closePool()
        try:
            reactor.stop()
        except Exception as e:
            set_status_code(1)
            reactor.callLater(0, reactor.stop)


    # ---------------
    # OPERATIONAL API
    # ---------------

    def quit(self, exit_code = 0):
        set_status_code(exit_code)
        reactor.callLater(0, self.parent.stopService)

    # =============
    # Twisted Tasks
    # =============
   
        

      
    # ==============
    # Helper methods
    # ==============

    def openPool(self):
        # setup the connection pool for asynchronouws adbapi
        log.debug("Opening DB Connection to {conn!s}", conn=self.path)
        self.pool  = self.getPoolFunc(self.path)
        log.debug("Opened DB Connection to {conn!s}", conn=self.path)


    def closePool(self):
        '''setup the connection pool for asynchronouws adbapi'''
        log.debug("Closing DB Connection to {conn!s}", conn=self.path)
        self.pool.close()
        log.debug("Closed DB Connection to {conn!s}", conn=self.path)
