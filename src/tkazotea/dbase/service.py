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

from tkazotea import SQL_SCHEMA, SQL_INITIAL_DATA_DIR, SQL_UPDATES_DATA_DIR

from tkazotea.logger import setLogLevel
from tkazotea.dbase.dao import DataAccesObject

# ----------------
# Module constants
# ----------------

NAMESPACE = 'DBASE'

DATABASE_FILE = 'azotea.db'

SQL_TEST_STRING = "SELECT COUNT(*) FROM image_t"

# -----------------------
# Module global variables
# -----------------------

log = Logger(NAMESPACE)

# ------------------------
# Module Utility Functions
# ------------------------

def getPool(*args, **kargs):
    '''Get connetion pool for sqlite3 driver'''
    kargs['check_same_thread'] = False
    return adbapi.ConnectionPool("sqlite3", *args, **kargs)


def open_database(dbase_path):
    '''Creates a Database file if not exists and returns a connection'''
    output_dir = os.path.dirname(dbase_path)
    if not output_dir:
        output_dir = os.getcwd()
    os.makedirs(output_dir, exist_ok=True)
    if not os.path.exists(dbase_path):
        with open(dbase_path, 'w') as f:
            pass
        log.info("Created database file {0}".format(dbase_path))
    return sqlite3.connect(dbase_path)


def create_database(connection, schema_path, initial_data_dir_path, updates_data_dir, query):
    created = True
    cursor = connection.cursor()
    try:
        cursor.execute(query)
    except Exception:
        created = False
    if not created:
        with open(schema_path) as f: 
            lines = f.readlines() 
        script = ''.join(lines)
        connection.executescript(script)
        log.info("Created data model from {0}".format(os.path.basename(schema_path)))
        file_list = glob.glob(os.path.join(initial_data_dir_path, '*.sql'))
        for sql_file in file_list:
            log.info("Populating data model from {0}".format(os.path.basename(sql_file)))
            with open(sql_file) as f: 
                lines = f.readlines() 
            script = ''.join(lines)
            connection.executescript(script)
    else:
        file_list = glob.glob(os.path.join(updates_data_dir, '*.sql'))
        for sql_file in file_list:
            log.info("Applying updates to data model from {0}".format(os.path.basename(sql_file)))
            with open(sql_file) as f: 
                lines = f.readlines() 
            script = ''.join(lines)
            connection.executescript(script)
    connection.commit()

def read_database_version(connection):
    cursor = connection.cursor()
    query = 'SELECT value FROM config_t WHERE section = "database" AND property = "version";'
    cursor.execute(query)
    version = cursor.fetchone()[0]
    return version

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

    def __init__(self, path, **kargs):
        super().__init__()   
        setLogLevel(namespace=NAMESPACE, levelStr='info')
        self.path = path
        self.pool = None
        self.preferences = None
        self.getPoolFunc = getPool
    
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
        log.info("Starting Database Service on {database}", database=self.path)
        connection = open_database(self.path)
        create_database(connection, SQL_SCHEMA, SQL_INITIAL_DATA_DIR, SQL_UPDATES_DATA_DIR, SQL_TEST_STRING)
        levels  = read_debug_levels(connection)
        version = read_database_version(connection)
        pub.subscribe(self.quit,  'file_quit')
        # Remainder Service initialization
        super().startService()
        connection.commit()
        connection.close()
        self.openPool()
        self.dao = DataAccesObject(self.pool, *levels)
        self.dao.version = version
        return self.foreign_keys(True)


    def stopService(self):
        log.info("Stopping Database Service")
        self.closePool()
        try:
            reactor.stop()
        except Exception as e:
            reactor.callLater(0, reactor.stop)


    # ---------------
    # OPERATIONAL API
    # ---------------

    def quit(self):
        reactor.callLater(0, self.parent.stopService)

    # =============
    # Twisted Tasks
    # =============
   
        

      
    # ==============
    # Helper methods
    # ==============

    def openPool(self):
        # setup the connection pool for asynchronouws adbapi
        log.info("Opening DB Connection to {conn!s}", conn=self.path)
        self.pool  = self.getPoolFunc(self.path)
        log.debug("Opened DB Connection to {conn!s}", conn=self.path)


    def closePool(self):
        '''setup the connection pool for asynchronouws adbapi'''
        log.info("Closing DB Connection to {conn!s}", conn=self.path)
        self.pool.close()
        log.debug("Closed DB Connection to {conn!s}", conn=self.path)
