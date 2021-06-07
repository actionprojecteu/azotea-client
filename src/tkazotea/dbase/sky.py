# ----------------------------------------------------------------------
# Copyright (c) 2020
#
# See the LICENSE file for details
# see the AUTHORS file for authors
# ----------------------------------------------------------------------

#--------------------
# System wide imports
# -------------------

import base64
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

from tkazotea.logger import setLogLevel
from tkazotea.dbase.tables import Table, VersionedTable

# ----------------
# Module constants
# ----------------

NAMESPACE = 'DBASE'


class SkyBrightness:

    def __init__(self, pool, log_level):
        self._pool = pool
        self.log = Logger(namespace='sky_brightness_t')
        setLogLevel(namespace='sky_brightness_t', levelStr=log_level)


    def countAll(self, filter_dict):
        def _countAll(txn, filter_dict):
            sql = '''SELECT COUNT(*) FROM sky_brightness_t WHERE observer_id = :observer_id;'''
            txn.execute(sql, filter_dict)
            return txn.fetchone()[0]
        return self._pool.runInteraction(_countAll, filter_dict)

    def deleteAll(self, filter_dict):
        def _deleteAll(txn, filter_dict):
            sql = '''DELETE FROM sky_brightness_t WHERE observer_id = :observer_id;'''
            txn.execute(sql, filter_dict)
        return self._pool.runInteraction(_deleteAll, filter_dict)

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
            WHERE observer_id = :observer_id
            AND date_id BETWEEN :start_date_id AND :end_date_id;
            '''
            txn.execute(sql, filter_dict)
        return self._pool.runInteraction(_deleteDateRange, filter_dict)


    # For the time being, no filter
    def pending(self, filter_dict):
        def _pending(txn, filter_dict):
            sql = '''
                SELECT image_id
                FROM image_t
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
                    observer_id,
                    location_id,
                    camera_id,
                    image_id,
                    roi_id,
                    date_id,
                    time_id,
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
                    :observer_id,
                    :location_id,
                    :camera_id,
                    :image_id,
                    :roi_id,
                    :date_id,
                    :time_id,
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
            txn.execute(sql, row_dict)
        return self._pool.runInteraction(_save, row_dict)

    # To generate a file name
    def getLatestMonth(self, filter_dict):
        def _getLatestMonth(txn, filter_dict):
            sql = '''
            SELECT MAX(d.year),MAX(d.month_num),1
            FROM sky_brightness_t AS s
            JOIN date_t AS d USING(date_id)
            JOIN observer_t AS o USING(observer_id)
            WHERE s.observer_id = :observer_id
            '''
            self.log.debug(sql)
            txn.execute(sql, filter_dict)
            return txn.fetchone()
        return self._pool.runInteraction(_getLatestMonth, filter_dict)

    def getLatestMonthCount(self, filter_dict):
        def _getLatestMonthCount(txn, filter_dict):
            sql = '''
            SELECT COUNT(*)
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
            FROM sky_brightness_t AS s
            JOIN date_t AS d USING(date_id)
            JOIN time_t AS t USING(time_id)
            JOIN observer_t AS o USING(observer_id)
            WHERE o.observer_id = :observer_id
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
            FROM sky_brightness_t AS s
            JOIN date_t AS d USING(date_id)
            JOIN time_t AS t USING(time_id)
            JOIN observer_t AS o USING(observer_id)
            WHERE o.observer_id = :observer_id
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
            FROM sky_brightness_t AS s
            JOIN observer_t AS o USING(observer_id)
            WHERE s.observer_id = :observer_id
            AND s.date_id BETWEEN :start_date_id AND :end_date_id;
            '''
            self.log.debug(sql)
            txn.execute(sql, filter_dict)
            return txn.fetchone()[0]
        return self._pool.runInteraction(_getDateRangeCount, filter_dict)


    def exportAll(self, filter_dict):
        def _exportAll(txn, filter_dict):
            sql = '''
            SELECT 
            i.session,  
            o.surname || ', ' || o.family_name, 
            o.acronym, 
            l.site_name || ' - ' || l.location, 
            'LIGHT', -- image type
            d.sql_date || 'T' || t.time, 
            i.name, 
            c.model, 
            i.iso, 
            r.display_name,
            NULL,   -- dark roi 
            i.exptime,
            s.aver_signal_R,  
            s.vari_signal_R, 
            s.aver_signal_G1, 
            s.vari_signal_G1, 
            s.aver_signal_G2, 
            s.vari_signal_G2,
            s.aver_signal_B,  
            s.vari_signal_B,
            s.aver_dark_R,    
            s.vari_dark_R,
            s.aver_dark_G1,   
            s.vari_dark_G1,
            s.aver_dark_G2,   
            s.vari_dark_G2,
            s.aver_dark_B,    
            s.vari_dark_B,
            c.bias
            FROM sky_brightness_t AS s
            JOIN roi_t      AS r USING(roi_id)
            JOIN date_t     AS d USING(date_id)
            JOIN time_t     AS t USING(time_id)
            JOIN image_t    AS i USING(image_id)
            JOIN camera_t   AS c USING(camera_id)
            JOIN observer_t AS o USING(observer_id)
            JOIN location_t AS l USING(location_id)
            WHERE s.observer_id = :observer_id
            ORDER BY s.date_id ASC, s.time_id ASC;
            '''
            self.log.debug(sql)
            txn.execute(sql, filter_dict)
            return txn.fetchall()
        return self._pool.runInteraction(_exportAll, filter_dict)


    def exportDateRange(self, filter_dict):
        def _exportDateRange(txn, filter_dict):
            sql = '''
            SELECT 
            i.session,  
            o.surname || ', ' || o.family_name, 
            o.acronym, 
            l.site_name || ' - ' || l.location, 
            'LIGHT', -- image type
            d.sql_date || 'T' || t.time, 
            i.name, 
            c.model, 
            i.iso, 
            r.display_name,
            NULL,   -- dark roi 
            i.exptime,
            s.aver_signal_R,  
            s.vari_signal_R, 
            s.aver_signal_G1, 
            s.vari_signal_G1, 
            s.aver_signal_G2, 
            s.vari_signal_G2,
            s.aver_signal_B,  
            s.vari_signal_B,
            s.aver_dark_R,    
            s.vari_dark_R,
            s.aver_dark_G1,   
            s.vari_dark_G1,
            s.aver_dark_G2,   
            s.vari_dark_G2,
            s.aver_dark_B,    
            s.vari_dark_B,
            c.bias
            FROM sky_brightness_t AS s
            JOIN roi_t      AS r USING(roi_id)
            JOIN date_t     AS d USING(date_id)
            JOIN time_t     AS t USING(time_id)
            JOIN image_t    AS i USING(image_id)
            JOIN camera_t   AS c USING(camera_id)
            JOIN observer_t AS o USING(observer_id)
            JOIN location_t AS l USING(location_id)
            WHERE s.observer_id = :observer_id
            AND s.date_id BETWEEN :start_date_id AND :end_date_id
            ORDER BY s.date_id ASC, s.time_id ASC;
            '''
            self.log.debug(sql)
            txn.execute(sql, filter_dict)
            return txn.fetchall()
        return self._pool.runInteraction(_exportDateRange, filter_dict)


    def exportLatestNight(self, filter_dict):
        def _exportLatestNight(txn, filter_dict):
            sql = '''
            SELECT 
            i.session,  
            o.surname || ', ' || o.family_name, 
            o.acronym, 
            l.site_name || ' - ' || l.location, 
            'LIGHT', -- image type
            d.sql_date || 'T' || t.time, 
            i.name, 
            c.model, 
            i.iso, 
            r.display_name,
            NULL,   -- dark roi 
            i.exptime,
            s.aver_signal_R,  
            s.vari_signal_R, 
            s.aver_signal_G1, 
            s.vari_signal_G1, 
            s.aver_signal_G2, 
            s.vari_signal_G2,
            s.aver_signal_B,  
            s.vari_signal_B,
            s.aver_dark_R,    
            s.vari_dark_R,
            s.aver_dark_G1,   
            s.vari_dark_G1,
            s.aver_dark_G2,   
            s.vari_dark_G2,
            s.aver_dark_B,    
            s.vari_dark_B,
            c.bias
            FROM sky_brightness_t AS s
            JOIN roi_t  AS r USING(roi_id)
            JOIN date_t  AS d USING(date_id)
            JOIN time_t  AS t USING(time_id)
            JOIN image_t  AS i USING(image_id)
            JOIN camera_t AS c USING(camera_id)
            JOIN observer_t AS o USING(observer_id)
            JOIN location_t AS l USING(location_id)
            WHERE s.observer_id = :observer_id
            AND round((d.julian_day - 0.5 + t.day_fraction),0) = (
                SELECT MAX(round((d.julian_day - 0.5 + t.day_fraction),0))
                FROM image_t AS i
                JOIN date_t AS d USING(date_id)
                JOIN time_t AS t USING(time_id)
                JOIN observer_t AS o USING(observer_id)
                WHERE i.observer_id = :observer_id
            )
            ORDER BY s.date_id ASC, s.time_id ASC;
            '''
            self.log.debug(sql)
            txn.execute(sql, filter_dict)
            return txn.fetchall()
        return self._pool.runInteraction(_exportLatestNight, filter_dict)

    def exportLatestMonth(self, filter_dict):
        def _exportLatestMonth(txn, filter_dict):
            sql = '''
            SELECT 
            i.session,  
            o.surname || ', ' || o.family_name, 
            o.acronym, 
            l.site_name || ' - ' || l.location, 
            'LIGHT', -- image type
            d.sql_date || 'T' || t.time, 
            i.name, 
            c.model, 
            i.iso, 
            r.display_name,
            NULL,   -- dark roi 
            i.exptime,
            s.aver_signal_R,  
            s.vari_signal_R, 
            s.aver_signal_G1, 
            s.vari_signal_G1, 
            s.aver_signal_G2, 
            s.vari_signal_G2,
            s.aver_signal_B,  
            s.vari_signal_B,
            s.aver_dark_R,    
            s.vari_dark_R,
            s.aver_dark_G1,   
            s.vari_dark_G1,
            s.aver_dark_G2,   
            s.vari_dark_G2,
            s.aver_dark_B,    
            s.vari_dark_B,
            c.bias
            FROM sky_brightness_t AS s
            JOIN roi_t  AS r USING(roi_id)
            JOIN date_t  AS d USING(date_id)
            JOIN time_t  AS t USING(time_id)
            JOIN image_t  AS i USING(image_id)
            JOIN camera_t AS c USING(camera_id)
            JOIN observer_t AS o USING(observer_id)
            JOIN location_t AS l USING(location_id)
            WHERE s.observer_id = :observer_id
            AND d.month_num = (
                SELECT MAX(d.month_num)
                FROM sky_brightness_t AS s
                JOIN date_t AS d USING(date_id)
                JOIN observer_t AS o USING(observer_id)
                WHERE s.observer_id = :observer_id
            )
            AND d.year = (
                SELECT MAX(d.year)
                FROM sky_brightness_t AS s
                JOIN date_t AS d USING(date_id)
                JOIN observer_t AS o USING(observer_id)
                WHERE s.observer_id = :observer_id
            )
            ORDER BY s.date_id ASC, s.time_id ASC;
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
            JOIN observer_t AS o USING(observer_id)
            WHERE s.observer_id = :observer_id
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
            WHERE observer_id = :observer_id
            AND published = 0;
            '''
            self.log.debug(sql)
            txn.execute(sql, filter_dict)
            return txn.fetchone()[0]
        return self._pool.runInteraction(_updatePublishingCount, filter_dict)

    pub_column_names = ('date_id','time_id',
        'surname','family_name','acronym','affiliation','valid_since','valid_until','valid_state',
        'site_name','location','public_long','public_lat','utc_offset',
        'model','bias','extension','header_type','bayer_pattern','width','length',
        'x1','y1','x2','y2','display_name','comment',
        'name','directory','hash','iso','gain','exptime','focal_length','f_number','session',
        'aver_signal_R','vari_signal_R','aver_signal_G1','vari_signal_G1',
        'aver_signal_G2','vari_signal_G2','aver_signal_B','vari_signal_B')


    def publishAll(self, filter_dict):

        def toBase64(aDict):
            aDict['hash'] = base64.b64encode(aDict['hash']).decode('ascii')
            return aDict

        def _publishAll(txn, filter_dict):
            sql = '''
            SELECT
            s.date_id, s.time_id,
            o.surname, o.family_name, o.acronym, o.affiliation, o.valid_since, o.valid_until, o.valid_state,
            l.site_name, l.location, l.public_long, l.public_lat, l.utc_offset,
            c.model, c.bias, c.extension, c.header_type, c.bayer_pattern, c.width, c.length,
            r.x1, r.y1, r.x2, r.y2, r.display_name, r.comment,
            i.name, i.directory, i.hash, i.iso, i.gain, i.exptime, i.focal_length, i.f_number, i.session,  
            s.aver_signal_R,  s.vari_signal_R,  s.aver_signal_G1, s.vari_signal_G1, 
            s.aver_signal_G2, s.vari_signal_G2, s.aver_signal_B,  s.vari_signal_B
            FROM sky_brightness_t AS s
            JOIN roi_t      AS r USING(roi_id)
            JOIN image_t    AS i USING(image_id)
            JOIN camera_t   AS c USING(camera_id)
            JOIN observer_t AS o USING(observer_id)
            JOIN location_t AS l USING(location_id)
            WHERE s.observer_id = :observer_id
            AND   s.published = 0
            ORDER BY s.date_id ASC, s.time_id ASC
            LIMIT :limit OFFSET :offset;
            '''
            self.log.debug(sql)
            txn.execute(sql, filter_dict)
            result = [dict(zip(self.pub_column_names,row)) for row in txn.fetchall()]
            return list(map(toBase64, result))
        return self._pool.runInteraction(_publishAll, filter_dict)


    