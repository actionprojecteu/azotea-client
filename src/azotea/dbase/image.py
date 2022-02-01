# ----------------------------------------------------------------------
# Copyright (c) 2020
#
# See the LICENSE file for details
# see the AUTHORS file for authors
# ----------------------------------------------------------------------

#--------------------
# System wide imports
# -------------------

import sqlite3
import datetime

# ---------------
# Twisted imports
# ---------------

from twisted.logger import Logger
from twisted.enterprise import adbapi

#--------------
# local imports
# -------------

from azotea.logger import setLogLevel
from azotea.dbase.tables import Table, VersionedTable

# ----------------
# Module constants
# ----------------


class ImageTable(Table):

    def _sqlInsert(self):
        '''This is not INSERT OR REPLACE. let the hash UNIQUE constraint do their work'''
        table = self._table 
        column_list = self._natural_key_columns + self._other_columns
        all_values = ",".join([f":{column}" for column in column_list])
        all_columns = ",".join(column_list)
        sql = f"INSERT INTO {table} ({all_columns}) VALUES ({all_values});"
        self.log.debug("{sql}", sql=sql)
        return sql

    def flagAsBad(self, filter_dict):
        '''Flag as bad image'''
        def _flagAsBad(txn, filter_dict):
            txn.execute(
                '''
                UPDATE image_t
                SET flagged = 1
                WHERE image_id = :image_id
                ''',filter_dict)
        return self._pool.runInteraction(_flagAsBad, filter_dict)
    
    def fixDirectory(self, filter_dict):
        def _fixDirectory(txn, filter_dict):
            txn.execute(
                '''
                UPDATE image_t
                SET directory = :directory
                WHERE name = :name AND hash = :hash
                ''',filter_dict)
            '''Fixes directory in case of file movement'''
        return self._pool.runInteraction(_fixDirectory, filter_dict)

    def getByHash(self, filter_dict):
        def _getByHash(txn, filter_dict):
            sql = '''
                SELECT name, directory
                FROM image_t
                WHERE hash = :hash;
            '''
            txn.execute(sql, filter_dict)
            return txn.fetchone()
        return self._pool.runInteraction(_getByHash, filter_dict)


    # This only happens when we edit *in-place* an image after being loaded by AZOTEA
    # This is the case for FITS files being post-edited to add new keyword values
    # we don't do this for EXIF files.
    def purgeDuplicates(self):
        '''Purge images with the same path and different hashes'''
        def _purgeDuplicates(txn):
            # We must delete foreign key referernces first
            txn.execute(
                '''
                DELETE FROM sky_brightness_t
                WHERE image_id IN (
                    SELECT image_id 
                    FROM image_t 
                    GROUP BY directory, name 
                    HAVING count(*) > 1 AND session = MIN(session)
                    );
                '''
            )
            txn.execute(
                '''
                DELETE FROM image_t
                WHERE image_id IN (
                    SELECT image_id 
                    FROM image_t 
                    GROUP BY directory, name 
                    HAVING count(*) > 1 AND session = MIN(session)
                );
                '''
            )
        return self._pool.runInteraction(_purgeDuplicates)


    def imagesInDirectory(self, filter_dict):
        '''Gets all the metadata needed for sky brightness mmeasurements'''
        def _imagesInDirectory(txn, filter_dict):
            sql = '''
                SELECT name
                FROM image_t
                WHERE directory = :directory;
            '''
            txn.execute(sql, filter_dict)
            return txn.fetchall()
        return self._pool.runInteraction(_imagesInDirectory, filter_dict)
    
    def getInitialMetadata(self, filter_dict):
        '''Gets all the metadata needed for sky brightness mmeasurements'''
        def _getInitialMetadata(txn, filter_dict):
            sql = '''
                SELECT i.name, i.directory, c.header_type, i.exptime, c.bayer_pattern, i.camera_id,  i.date_id, i.time_id, i.observer_id, i.location_id
                FROM image_t AS i
                JOIN camera_t AS c USING (camera_id)
                WHERE i.image_id = :image_id;
            '''
            txn.execute(sql, filter_dict)
            return txn.fetchone()
        return self._pool.runInteraction(_getInitialMetadata, filter_dict)

    def summaryStatistics(self):
        def _summaryStatistics(txn):
            sql = '''
                SELECT o.surname, o.family_name, i.imagetype, i.flagged, count(*) as cnt 
                FROM image_t AS i
                JOIN observer_t AS o USING(observer_id)
                GROUP BY observer_id, i.imagetype, i.flagged
                ORDER BY o.surname, o.family_name, i.imagetype, cnt DESC'''
            txn.execute(sql)
            return txn.fetchall()
        return self._pool.runInteraction(_summaryStatistics)

    def rangeSummary(self):
        def _rangeSummary(txn):
            sql = '''
                SELECT o.surname, o.family_name, MIN(d.sql_date), MAX(d.sql_date), count(*) as cnt 
                FROM image_t AS i
                JOIN observer_t AS o USING(observer_id)
                JOIN date_t AS d USING(date_id)
                GROUP BY observer_id
                ORDER BY o.surname, o.family_name'''
            txn.execute(sql)
            return txn.fetchall()
        return self._pool.runInteraction(_rangeSummary)
