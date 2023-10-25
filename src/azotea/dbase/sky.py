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

PUB_COLUMN_NAMES = (
    # L = 1
    'uuid',     # uuid[0:1]
    # L = 1
    'date_id', # date [1:2]
    # L = 1
    'time_id', # time [2:3]
    # L = 7
    'surname','family_name','acronym','affiliation','valid_since','valid_until','valid_state', # observer [3:10]
    # L = 6
    'site_name','location','longitude','latitude', 'randomized', 'utc_offset',                 # location [10:16]
    # L = 9
    'model','bias','extension','header_type','bayer_pattern','width','length', 'x_pixsize', 'y_pixsize', # camera [16:25]
    # L = 6
    'x1', 'y1', 'x2', 'y2' ,'display_name','comment',                                              # roi [25:31]
    # L = 11
    'name','directory','hash','iso','gain','exptime','focal_length','f_number', 'imagetype', 'flagged', 'session', # image [31:42]
    # L = 8
    'aver_signal_R','vari_signal_R','aver_signal_G1','vari_signal_G1',                         # sky_brightness [42:50]
    'aver_signal_G2','vari_signal_G2','aver_signal_B','vari_signal_B'
)


# ------------------------
# Module Utility Functions
# ------------------------

def slice_func(row):
    '''Slices a row into separate components for JSON publishing'''
    #print(f"ROW  = {tuple(zip(row, range(len(row)) ))}")
    result = {
        'uuid'           : row[0:1][0], # the slice is a tuple
        'date'           : row[1:2][0], # the slice is a tuple
        'time'           : row[2:3][0], # the slice is a tuple
        'observer'       : dict(zip(PUB_COLUMN_NAMES[3:10],  row[3:10])),
        'location'       : dict(zip(PUB_COLUMN_NAMES[10:16], row[10:16])),
        'camera'         : dict(zip(PUB_COLUMN_NAMES[16:25], row[16:25])),
        'roi'            : dict(zip(PUB_COLUMN_NAMES[25:31], row[25:31])),
        'image'          : dict(zip(PUB_COLUMN_NAMES[31:42], row[31:42])),
        'sky_brightness' : dict(zip(PUB_COLUMN_NAMES[42:50], row[42:50])),
    }
    result['image']['hash'] = result['image']['hash'].hex()
    return result   


CSV_VERSION = 2

class SkyBrightness:

    def __init__(self, pool, log_level):
        self._pool = pool
        self.log = Logger(namespace='sky_brightness_t')
        setLogLevel(namespace='sky_brightness_t', levelStr=log_level)


    def summaryStatistics(self):
        def _summaryStatistics(txn):
            sql = '''
                SELECT o.surname, o.family_name, s.display_name, s.width, s.height, s.published, count(*) as cnt
                FROM image_t AS i
                JOIN observer_t AS o USING(observer_id)
                JOIN sky_brightness_v AS s USING(image_id)
                GROUP BY observer_id,  s.display_name --, s.published # I don't know why this is not working
                ORDER BY o.surname, s.display_name, cnt DESC'''
            txn.execute(sql)
            return txn.fetchall()
        return self._pool.runInteraction(_summaryStatistics)

    def rangeSummary(self):
        def _rangeSummary(txn):
            sql = '''
                SELECT o.surname, o.family_name, MIN(d.sql_date), MAX(d.sql_date), count(*) as cnt
                FROM image_t AS i
                JOIN observer_t AS o USING(observer_id)
                JOIN sky_brightness_v AS s USING(image_id)
                JOIN date_t AS d USING(date_id)
                GROUP BY observer_id
                ORDER BY o.surname, o.family_name'''
            txn.execute(sql)
            return txn.fetchall()
        return self._pool.runInteraction(_rangeSummary)

    def countAll(self, filter_dict):
        def _countAll(txn, filter_dict):
            sql = '''
                SELECT COUNT(*) FROM sky_brightness_t AS s
                JOIN image_t AS i USING(image_id)
                WHERE i.observer_id = :observer_id;'''
            txn.execute(sql, filter_dict)
            return txn.fetchone()[0]
        return self._pool.runInteraction(_countAll, filter_dict)

    def deleteAll(self, filter_dict):
        def _deleteAll(txn, filter_dict):
            sql = '''
                DELETE FROM sky_brightness_t 
                WHERE image_id IN (
                    SELECT image_id FROM image_t 
                    WHERE observer_id = :observer_id
                )
                '''
            txn.execute(sql, filter_dict)
        return self._pool.runInteraction(_deleteAll, filter_dict)


    def deleteUnpublished(self, filter_dict):
        def _deleteUnpublished(txn, filter_dict):
            sql = '''
                DELETE FROM sky_brightness_t 
                WHERE image_id IN (
                    SELECT image_id FROM image_t 
                    WHERE observer_id = :observer_id
                ) AND published = 0
                '''
            txn.execute(sql, filter_dict)
        return self._pool.runInteraction(_deleteUnpublished, filter_dict)


    def deleteLatestNight(self, filter_dict):
        def _deleteLatestNight(txn, filter_dict):
            sql = '''DELETE FROM sky_brightness_t
            WHERE image_id IN (
                SELECT i.image_id 
                FROM image_t AS i
                JOIN date_t AS d USING(date_id)
                JOIN time_t AS t USING(time_id)
                JOIN observer_t AS o USING(observer_id)
                WHERE i.observer_id = :observer_id
                AND round((d.julian_day - 0.5 + t.day_fraction),0) = (
                    SELECT MAX(round((d.julian_day - 0.5 + t.day_fraction),0))
                    FROM image_t AS i
                    JOIN date_t AS d USING(date_id)
                    JOIN time_t AS t USING(time_id)
                    JOIN observer_t AS o USING(observer_id)
                    WHERE i.observer_id = :observer_id
                )
            )
            '''
            txn.execute(sql, filter_dict)
        return self._pool.runInteraction(_deleteLatestNight, filter_dict)

    def deleteLatestMonth(self, filter_dict):
        def _deleteLatestMonth(txn, filter_dict):
            sql = '''DELETE FROM sky_brightness_t
            WHERE image_id IN (
                SELECT image_id
                FROM sky_brightness_t AS s
                JOIN date_t AS d USING(date_id)
                JOIN observer_t AS o USING(observer_id)
                WHERE s.observer_id = :observer_id
                AND d.year = (
                    SELECT MAX(d.year)
                    FROM sky_brightness_t AS s
                    JOIN date_t AS d USING(date_id)
                    JOIN observer_t AS o USING(observer_id)
                    WHERE s.observer_id = :observer_id
                )
                AND d.month_num = (
                    SELECT MAX(d.month_num)
                    FROM sky_brightness_t AS s
                    JOIN date_t AS d USING(date_id)
                    JOIN observer_t AS o USING(observer_id)
                    WHERE s.observer_id = :observer_id
                )
            )
            '''
            txn.execute(sql, filter_dict)
        return self._pool.runInteraction(_deleteLatestMonth, filter_dict)

    def deleteDateRange(self, filter_dict):
        def _deleteDateRange(txn, filter_dict):
            sql = '''
            DELETE FROM sky_brightness_t
            WHERE image_id IN (
                SELECT image_id FROM image_t
                WHERE observer_id = :observer_id
                AND date_id BETWEEN :start_date_id AND :end_date_id
            )
            '''
            txn.execute(sql, filter_dict)
        return self._pool.runInteraction(_deleteDateRange, filter_dict)


    # For the time being, no filter
    def pending(self, filter_dict):
        def _pending(txn, filter_dict):
            sql = '''
                SELECT image_id
                FROM image_t
                WHERE flagged = 0
                AND observer_id = :observer_id
                EXCEPT 
                SELECT DISTINCT image_id 
                FROM sky_brightness_t;
            '''
            self.log.debug(sql)
            txn.execute(sql, filter_dict)
            return txn.fetchall()
        return self._pool.runInteraction(_pending, filter_dict)

    def save(self, row_dict):
        def _save(txn, row_dict):
            sql = '''
                INSERT INTO sky_brightness_t (
                    image_id,
                    roi_id,
                    aver_signal_R,
                    vari_signal_R,
                    aver_signal_G1,
                    vari_signal_G1,
                    aver_signal_G2,
                    vari_signal_G2,
                    aver_signal_B,
                    vari_signal_B
                )
                VALUES (
                    :image_id,
                    :roi_id,
                    :aver_signal_R,
                    :vari_signal_R,
                    :aver_signal_G1,
                    :vari_signal_G1,
                    :aver_signal_G2,
                    :vari_signal_G2,
                    :aver_signal_B,
                    :vari_signal_B
                )
            '''
            self.log.debug(sql)
            if type(row_dict) in (list, tuple):
                txn.executemany(sql, row_dict)
            else:
                txn.execute(sql, row_dict)
        return self._pool.runInteraction(_save, row_dict)

    # To generate a file name
    def getLatestMonth(self, filter_dict):
        def _getLatestMonth(txn, filter_dict):
            sql = '''
            SELECT MAX(d.year),MAX(d.month_num),1
            FROM image_t AS i
            JOIN date_t AS d USING(date_id)
            JOIN observer_t AS o USING(observer_id)
            WHERE i.observer_id = :observer_id
            '''
            self.log.debug(sql)
            txn.execute(sql, filter_dict)
            return txn.fetchone()
        return self._pool.runInteraction(_getLatestMonth, filter_dict)

    def getLatestMonthCount(self, filter_dict):
        def _getLatestMonthCount(txn, filter_dict):
            sql = '''
            SELECT COUNT(*)
            FROM image_t AS i
            JOIN date_t AS d USING(date_id)
            JOIN observer_t AS o USING(observer_id)
            WHERE i.observer_id = :observer_id
            AND d.year = (
                SELECT MAX(d.year)
                FROM image_t AS i
                JOIN date_t AS d USING(date_id)
                JOIN observer_t AS o USING(observer_id)
                WHERE i.observer_id = :observer_id
            )
            AND d.month_num = (
                SELECT MAX(d.month_num)
                FROM image_t AS i
                JOIN date_t AS d USING(date_id)
                JOIN observer_t AS o USING(observer_id)
                WHERE i.observer_id = :observer_id
            )
            '''
            self.log.debug(sql)
            txn.execute(sql, filter_dict)
            return txn.fetchone()[0]
        return self._pool.runInteraction(_getLatestMonthCount, filter_dict)

    # To generate a file name
    def getLatestNight(self, filter_dict):
        def _getLatestNight(txn, filter_dict):
            sql = '''
            SELECT d.year, d.month_num, d.day
            FROM image_t AS i
            JOIN date_t AS d USING(date_id)
            JOIN time_t AS t USING(time_id)
            JOIN observer_t AS o USING(observer_id)
            WHERE i.observer_id = :observer_id
            AND round((d.julian_day - 0.5 + t.day_fraction),0) = (
                SELECT MAX(round((d.julian_day - 0.5 + t.day_fraction),0))
                FROM image_t AS i
                JOIN date_t AS d USING(date_id)
                JOIN time_t AS t USING(time_id)
                JOIN observer_t AS o USING(observer_id)
                WHERE i.observer_id = :observer_id
            )
            '''
            self.log.debug(sql)
            txn.execute(sql, filter_dict)
            return txn.fetchone()
        return self._pool.runInteraction(_getLatestNight, filter_dict)

    def getLatestNightCount(self, filter_dict):
        def _getLatestNightCount(txn, filter_dict):
            sql = '''
            SELECT count(*)
            FROM image_t AS i
            JOIN date_t AS d USING(date_id)
            JOIN time_t AS t USING(time_id)
            JOIN observer_t AS o USING(observer_id)
            WHERE i.observer_id = :observer_id
            AND round((d.julian_day - 0.5 + t.day_fraction),0) = (
                SELECT MAX(round((d.julian_day - 0.5 + t.day_fraction),0))
                FROM image_t AS i
                JOIN date_t AS d USING(date_id)
                JOIN time_t AS t USING(time_id)
                JOIN observer_t AS o USING(observer_id)
                WHERE i.observer_id = :observer_id
            )
            '''
            self.log.debug(sql)
            txn.execute(sql, filter_dict)
            return txn.fetchone()[0]
        return self._pool.runInteraction(_getLatestNightCount, filter_dict)

    def getDateRangeCount(self, filter_dict):
        def _getDateRangeCount(txn, filter_dict):
            sql = '''
            SELECT COUNT(*)
            FROM image_t AS i
            JOIN observer_t AS o USING(observer_id)
            WHERE i.observer_id = :observer_id
            AND i.date_id BETWEEN :start_date_id AND :end_date_id;
            '''
            self.log.debug(sql)
            txn.execute(sql, filter_dict)
            return txn.fetchone()[0]
        return self._pool.runInteraction(_getDateRangeCount, filter_dict)


    def exportAll(self, filter_dict):
        def _exportAll(txn, filter_dict):
            filter_dict['csv_version'] = CSV_VERSION
            sql = '''
            SELECT 
            :csv_version,
            i.session,  
            o.surname || ', ' || o.family_name, 
            o.acronym, 
            l.site_name || ' - ' || l.location, 
            i.imagetype, -- image type
            d.sql_date || 'T' || t.time, 
            i.name, 
            c.model, 
            i.iso, 
            s.display_name,
            i.exptime,
            s.aver_signal_R,  
            s.vari_signal_R, 
            s.aver_signal_G1, 
            s.vari_signal_G1, 
            s.aver_signal_G2, 
            s.vari_signal_G2,
            s.aver_signal_B,  
            s.vari_signal_B,
            c.bias
            FROM image_t AS i
            JOIN sky_brightness_v AS s USING(image_id)
            JOIN date_t     AS d USING(date_id)
            JOIN time_t     AS t USING(time_id)
            JOIN camera_t   AS c USING(camera_id)
            JOIN observer_t AS o USING(observer_id)
            JOIN location_t AS l USING(location_id)
            WHERE i.observer_id = :observer_id
            ORDER BY i.date_id ASC, i.time_id ASC;
            '''
            self.log.debug(sql)
            txn.execute(sql, filter_dict)
            return txn.fetchall()
        return self._pool.runInteraction(_exportAll, filter_dict)


    def exportUnpublished(self, filter_dict):
        def _exportUnpublished(txn, filter_dict):
            filter_dict['csv_version'] = CSV_VERSION
            sql = '''
            SELECT 
            :csv_version,
            i.session,  
            o.surname || ', ' || o.family_name, 
            o.acronym, 
            l.site_name || ' - ' || l.location, 
            i.imagetype, -- image type
            d.sql_date || 'T' || t.time, 
            i.name, 
            c.model, 
            i.iso, 
            s.display_name,
            i.exptime,
            s.aver_signal_R,  
            s.vari_signal_R, 
            s.aver_signal_G1, 
            s.vari_signal_G1, 
            s.aver_signal_G2, 
            s.vari_signal_G2,
            s.aver_signal_B,  
            s.vari_signal_B,
            c.bias
            FROM image_t AS i
            JOIN sky_brightness_v AS s USING(image_id)
            JOIN date_t     AS d USING(date_id)
            JOIN time_t     AS t USING(time_id)
            JOIN camera_t   AS c USING(camera_id)
            JOIN observer_t AS o USING(observer_id)
            JOIN location_t AS l USING(location_id)
            WHERE  s.published = 0
            AND i.observer_id = :observer_id
            ORDER BY i.date_id ASC, i.time_id ASC;
            '''
            self.log.debug(sql)
            txn.execute(sql, filter_dict)
            return txn.fetchall()
        return self._pool.runInteraction(_exportUnpublished, filter_dict)


    def exportDateRange(self, filter_dict):
        def _exportDateRange(txn, filter_dict):
            filter_dict['csv_version'] = CSV_VERSION
            sql = '''
            SELECT 
            :csv_version,
            i.session,  
            o.surname || ', ' || o.family_name, 
            o.acronym, 
            l.site_name || ' - ' || l.location, 
            i.imagetype, -- image type
            d.sql_date || 'T' || t.time, 
            i.name, 
            c.model, 
            i.iso, 
            s.display_name,
            i.exptime,
            s.aver_signal_R,  
            s.vari_signal_R, 
            s.aver_signal_G1, 
            s.vari_signal_G1, 
            s.aver_signal_G2, 
            s.vari_signal_G2,
            s.aver_signal_B,  
            s.vari_signal_B,
            c.bias
            FROM image_t    AS i
            JOIN date_t     AS d USING(date_id)
            JOIN time_t     AS t USING(time_id)
            JOIN sky_brightness_v AS s USING(image_id)
            JOIN camera_t   AS c USING(camera_id)
            JOIN observer_t AS o USING(observer_id)
            JOIN location_t AS l USING(location_id)
            WHERE i.observer_id = :observer_id
            AND i.date_id BETWEEN :start_date_id AND :end_date_id
            ORDER BY i.date_id ASC, i.time_id ASC;
            '''
            self.log.debug(sql)
            txn.execute(sql, filter_dict)
            return txn.fetchall()
        return self._pool.runInteraction(_exportDateRange, filter_dict)


    def exportLatestNight(self, filter_dict):
        def _exportLatestNight(txn, filter_dict):
            filter_dict['csv_version'] = CSV_VERSION
            sql = '''
            SELECT 
            :csv_version,
            i.session,  
            o.surname || ', ' || o.family_name, 
            o.acronym, 
            l.site_name || ' - ' || l.location, 
            i.imagetype, -- image type
            d.sql_date || 'T' || t.time, 
            i.name, 
            c.model, 
            i.iso, 
            s.display_name,
            i.exptime,
            s.aver_signal_R,  
            s.vari_signal_R, 
            s.aver_signal_G1, 
            s.vari_signal_G1, 
            s.aver_signal_G2, 
            s.vari_signal_G2,
            s.aver_signal_B,  
            s.vari_signal_B,
            c.bias
            FROM image_t AS i
            JOIN sky_brightness_v  AS s USING(image_id) -- this is a view !
            JOIN date_t  AS d USING(date_id)
            JOIN time_t  AS t USING(time_id)
            JOIN camera_t AS c USING(camera_id)
            JOIN observer_t AS o USING(observer_id)
            JOIN location_t AS l USING(location_id)
            WHERE i.observer_id = :observer_id
            AND round((d.julian_day - 0.5 + t.day_fraction),0) = (
                SELECT MAX(round((d.julian_day - 0.5 + t.day_fraction),0))
                FROM image_t AS i
                JOIN date_t AS d USING(date_id)
                JOIN time_t AS t USING(time_id)
                JOIN observer_t AS o USING(observer_id)
                WHERE i.observer_id = :observer_id
            )
            ORDER BY i.date_id ASC, i.time_id ASC;
            '''
            self.log.debug(sql)
            txn.execute(sql, filter_dict)
            return txn.fetchall()
        return self._pool.runInteraction(_exportLatestNight, filter_dict)

    def exportLatestMonth(self, filter_dict):
        def _exportLatestMonth(txn, filter_dict):
            filter_dict['csv_version'] = CSV_VERSION
            sql = '''
            SELECT 
            :csv_version,
            i.session,  
            o.surname || ', ' || o.family_name, 
            o.acronym, 
            l.site_name || ' - ' || l.location, 
            i.imagetype, -- image type
            d.sql_date || 'T' || t.time, 
            i.name, 
            c.model, 
            i.iso, 
            s.display_name,
            i.exptime,
            s.aver_signal_R,  
            s.vari_signal_R, 
            s.aver_signal_G1, 
            s.vari_signal_G1, 
            s.aver_signal_G2, 
            s.vari_signal_G2,
            s.aver_signal_B,  
            s.vari_signal_B,
            c.bias
            FROM image_t AS i
            JOIN date_t  AS d USING(date_id)
            JOIN time_t  AS t USING(time_id)
            JOIN sky_brightness_v  AS s USING(image_id)
            JOIN camera_t AS c USING(camera_id)
            JOIN observer_t AS o USING(observer_id)
            JOIN location_t AS l USING(location_id)
            WHERE i.observer_id = :observer_id
            AND d.month_num = (
                SELECT MAX(d.month_num)
                FROM image_t AS i
                JOIN date_t AS d USING(date_id)
                JOIN observer_t AS o USING(observer_id)
                WHERE i.observer_id = :observer_id
            )
            AND d.year = (
                SELECT MAX(d.year)
                FROM image_t AS i
                JOIN date_t AS d USING(date_id)
                JOIN observer_t AS o USING(observer_id)
                WHERE i.observer_id = :observer_id
            )
            ORDER BY i.date_id ASC, i.time_id ASC;
            '''
            self.log.debug(sql)
            txn.execute(sql, filter_dict)
            return txn.fetchall()
        return self._pool.runInteraction(_exportLatestMonth, filter_dict)


    def getPublishingCount(self, filter_dict):
        def _getPublishingCount(txn, filter_dict):
            sql = '''
            SELECT COUNT(*)
            FROM sky_brightness_t AS s
            JOIN image_t AS i USING(image_id)
            WHERE i.observer_id = :observer_id
            AND s.published = 0;
            '''
            self.log.debug(sql)
            txn.execute(sql, filter_dict)
            return txn.fetchone()[0]
        return self._pool.runInteraction(_getPublishingCount, filter_dict)


    def updatePublishingCount(self, filter_dict):
        def _updatePublishingCount(txn, filter_dict):
            sql = '''
            UPDATE sky_brightness_t
            SET published = 1
            WHERE published = 0
            AND image_id IN (
                SELECT image_id FROM image_t
                WHERE  observer_id = :observer_id
                -- creo que no hace falta comprobar el flagged status
            )
            '''
            self.log.debug(sql)
            txn.execute(sql, filter_dict)
            return txn.fetchone()[0]
        return self._pool.runInteraction(_updatePublishingCount, filter_dict)


    def getAll(self, filter_dict):
        '''Get all data for publishing to server. filter_dict contains "observer_id", offset", "limit and "uuid"'''

        def _getAll(txn, filter_dict):
            sql = '''
            SELECT
            :uuid,
            i.date_id, i.time_id,
            o.surname, o.family_name, o.acronym, o.affiliation, o.valid_since, o.valid_until, o.valid_state,
            l.site_name, l.location, l.longitude, l.latitude, l.randomized, l.utc_offset,
            c.model, c.bias, c.extension, c.header_type, c.bayer_pattern, c.width, c.length, c.x_pixsize, c.y_pixsize,
            s.x1, s.y1, s.x2, s.y2, s.display_name, s.comment,
            i.name, i.directory, i.hash, i.iso, i.gain, i.exptime, i.focal_length, i.f_number, i.imagetype, i.flagged, i.session,  
            s.aver_signal_R,  s.vari_signal_R,  s.aver_signal_G1, s.vari_signal_G1, 
            s.aver_signal_G2, s.vari_signal_G2, s.aver_signal_B,  s.vari_signal_B
            FROM image_t AS i
            JOIN sky_brightness_v AS s USING(image_id)
            JOIN camera_t   AS c USING(camera_id)
            JOIN observer_t AS o USING(observer_id)
            JOIN location_t AS l USING(location_id)
            WHERE i.observer_id = :observer_id
            AND   s.published = 0
            -- ORDER BY i.date_id ASC, i.time_id ASC
            LIMIT :limit OFFSET :offset;
            '''
            self.log.debug(sql)
            txn.execute(sql, filter_dict) 
            return tuple(slice_func(row) for row in txn.fetchall())
        return self._pool.runInteraction(_getAll, filter_dict)


