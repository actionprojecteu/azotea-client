# ----------------------------------------------------------------------
# Copyright (c) 2021
#
# See the LICENSE file for details
# see the AUTHORS file for authors
# ----------------------------------------------------------------------

#--------------------
# System wide imports
# -------------------

import re
import os
import sys
import argparse
import sqlite3
import logging
import logging.handlers
import datetime
import traceback

#--------------
# local imports
# -------------

# ----------------
# Module constants
# ----------------

SQL_OLD_TEST = "SELECT COUNT(*) FROM state_t"
SQL_NEW_TEST = "SELECT COUNT(*) FROM observer_t"

BUFFER_SIZE = 100

LOCATION_DECODES = {
    'Madrid'                        : {'site_name': 'Madrid', 'location': 'Madrid'},
    'Riba-roja de Túria (Valencia)' : {'site_name': 'Riba-roja de Túria', 'location': 'Riba-roja de Túria'},
    'Requena (Valencia)'            : {'site_name': 'Requena', 'location': 'Requena'},
    'Villalba'                      : {'site_name': 'Villalba', 'location': 'Villalba'},
    'Madrid (Sur)'                  : {'site_name': '', 'location': 'Madrid'},
    'Fuerteventura'                 : {'site_name': 'Fuerteventura', 'location': 'Fuerteventura'},
    'Motilla del Palancar (Cuenca)' : {'site_name': 'Motilla del Palancar', 'location': 'Motilla del Palancar'},
    'Vitoria'                       : {'site_name': 'Vitoria', 'location': 'Vitoria'},
    'Hontecillas (Cuenca)'          : {'site_name': 'Hontecillas', 'location': 'Hontecillas'},
    'Mollerussa (Lleida)'           : {'site_name': 'Mollerussa', 'location': 'Mollerussa'},
    'Guadalajara (Centro)'          : {'site_name': 'Guadalajara (Centro)', 'location': 'Guadalajara'},
    'Villaverde del Ducado (Guadalajara)' : {'site_name': 'Villaverde del Ducado', 'location': 'Villaverde del Ducado'},
}

# -----------------------
# Module global variables
# -----------------------

__version__ = "0.1.0"

log = logging.getLogger("azotea")

save_list = list()

# --------------------------
# Module Azusiliar functions
# --------------------------

def configureLogging(options):
    if options.verbose:
        level = logging.DEBUG
    elif options.quiet:
        level = logging.WARN
    else:
        level = logging.INFO
    
    log.setLevel(level)
    # Log formatter
    #fmt = logging.Formatter('%(asctime)s - %(name)s [%(levelname)s] %(message)s')
    fmt = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
    # create console handler and set level to debug
    if not options.no_console:
        ch = logging.StreamHandler()
        ch.setFormatter(fmt)
        ch.setLevel(level)
        log.addHandler(ch)
    # Create a file handler Suitable for logrotate usage
    if options.log_file:
        #fh = logging.handlers.WatchedFileHandler(options.log_file)
        fh = logging.handlers.TimedRotatingFileHandler(options.log_file, when='midnight', interval=1, backupCount=365)
        fh.setFormatter(fmt)
        fh.setLevel(level)
        log.addHandler(fh)


def open_database(dbase_path):
    log.info("Opening database file {0}".format(dbase_path))
    return sqlite3.connect(dbase_path)


def check_database(connection, sql_string):
    cursor = connection.cursor()
    try:
        cursor.execute(sql_string)
    except Exception:
        raise TypeError("Wrong database")


def savemany_images(conn, rows):
    cursor = conn.cursor()
    sql = '''
    INSERT INTO image_t (
        name,           -- Image name without the path
        directory,      -- Directory path
        hash,           -- Image hash (alternative key in fact)
        iso,            -- DSLR ISO sensivity from EXIF
        gain,           -- For imagers that do not have ISO (i.e CMOS astrocameras saving in FITS)
        exptime,        -- exposure time in seconds from EXIF
        focal_length,   -- Either from configuration or EXIF
        f_number,       -- Either from configuration or EXIF
        imagetype,      -- Either 'LIGHT' or 'DARK'
        flagged,        -- 0 = image is ok, 1 = flagged as corrupt image
        session,        -- session identifier
        date_id,        -- decoded from tstamp & cached for later insert in in sky brightness table
        time_id,        -- decoded from tstamp & cached for later insert in in sky brightness table
        camera_id,      -- From EXIF lookup   
        location_id,    -- From default observer
        observer_id     -- From default location
    )
    VALUES (
        :name,
        :directory,
        :hash,
        :iso,
        :gain,
        :exptime,
        :focal_length,
        :f_number,
        :imagetype,
        :flagged,
        :session,
        :date_id,
        :time_id,
        :camera_id,
        :location_id,
        :observer_id
    )
    '''
    try:
        cursor.executemany(sql, rows)
    except sqlite3.IntegrityError as e:
        for row in rows:
            try:
                cursor.execute(sql, row)
            except  sqlite3.IntegrityError as e:
                log.error("Image already in new datrabase'{name}'", name=row['name'])
                continue


def savemany_sky(conn, rows):
    cursor = conn.cursor()
    sql = '''
    INSERT INTO sky_brightness_t (
        camera_id,      --  
        roi_id,         --  
        aver_signal_R,  -- R raw signal mean without dark substraction
        vari_signal_R , -- R raw signal variance without dark substraction
        aver_signal_G1, -- G1 raw signal mean without dark substraction
        vari_signal_G1, -- G1 raw signal variance without dark substraction
        aver_signal_G2, -- G2 raw signal mean without dark substraction
        vari_signal_G2, -- G2 raw signal variance without dark substraction
        aver_signal_B , -- B raw signal mean without dark substraction
        vari_signal_B,  -- B raw signal variance without dark substraction
        published      -- Published in server flag
    )
    VALUES (
        camera_id,      --  
        roi_id,         --  
        aver_signal_R,  -- R raw signal mean without dark substraction
        vari_signal_R , -- R raw signal variance without dark substraction
        aver_signal_G1, -- G1 raw signal mean without dark substraction
        vari_signal_G1, -- G1 raw signal variance without dark substraction
        aver_signal_G2, -- G2 raw signal mean without dark substraction
        vari_signal_G2, -- G2 raw signal variance without dark substraction
        aver_signal_B , -- B raw signal mean without dark substraction
        vari_signal_B,  -- B raw signal variance without dark substraction
        published      -- Published in server flag
    )
    '''
    try:
        cursor.executemany(sql, rows)
    except sqlite3.IntegrityError as e:
        for row in rows:
            try:
                cursor.execute(sql, row)
            except  sqlite3.IntegrityError as e:
                log.error("Sky brightness already in new datrabase'{name}'", name=row['name'])
                continue


def get_observer(newcon, row):
    cursor = newcon.cursor()
    sql = 'SELECT observer_id FROM observer_t WHERE valid_state = "Current" AND family_name = :family_name AND surname = :surname'
    cursor.execute(sql, row)
    result = cursor.fetchone()
    if result is None:
        raise ValueError(f"No observer id for {row['family_name']} {row['surname']}")
    return result[0]

def get_location(newcon, row):
    decodes = LOCATION_DECODES.get(row['location_old'], None)
    row['site_name'] = decodes['site_name']
    row['location']  = decodes['location']
    cursor = newcon.cursor()
    sql = 'SELECT location_id FROM location_t WHERE site_name = :site_name AND location = :location'
    log.info(f"ROW = {row}")
    cursor.execute(sql, row)
    result = cursor.fetchone()
    if result is None:
        raise ValueError(f"No location id for {row['site_name']} {row['location']}")
    return result[0]

def get_camera(newcon, row):
    cursor = newcon.cursor()
    sql = 'SELECT camera_id FROM camera_t WHERE model = :model'
    cursor.execute(sql, row)
    result = cursor.fetchone()
    if result is None:
        raise ValueError(f"No camera id for {row['model']}")
    return result[0]

def get_datetime(newcon, row):
    tstamp = datetime.strptime(row['tstamp'], '%Y-%m-%D')
    date_id = int(tstamp.strftime(tstamp, '%Y%m%D'))
    time_id = int(tstamp.strftime(tstamp, '%H%M%S'))
    return date_id, time_id

def get_roi(newcon, row):
    roi = row['display_name']
    regexp = re.compile(r'\[(\d+):(\d+),(\d+):(\d+)\]')
    matchobj = regexp.search(roi)
    if not matchobj:
        raise ValueError(f"ROI {roi} did not matchs the pattern")
    x1 = matchobj.group(1); x2 = matchobj.group(2);
    y1 = matchobj.group(3); y2 = matchobj.group(4);
    # Reverser ROY syntax for the new database (NumPy format)
    roi = f"[{y1}:{y2},{x1},{x2}]"
    cursor = newcon.cursor()
    sql = 'SELECT roi_id FROM roi_t WHERE display_name = :display_name'
    cursor.execute(sql, row)
    result = cursor.fetchone()
    if result is None:
        raise ValueError(f"No roi id for {row['display_name']}")
    return result[0]

def get_image_id_by_hash(newconn, row):
    cursor = newcon.cursor()
    sql = 'SELECT image_id FROM image_t WHERE hash = :hash'
    cursor.execute(sql, row)
    result = cursor.fetchone()
    if result is None:
        raise ValueError(f"No image id for hash {row['hash'].hex()}")
    return result[0]


def read_old_image(oldconn):
    cursor = oldconn.cursor()
    sql = '''
    SELECT
    -- Observer metadata
    obs_family_name, obs_surname,
    -- Location metadata
    location,
    -- Camera metadata
    model, focal_length, f_number,
    -- ROI metadata
    roi,      -- region of interest: [x1:x2,y1:y2]
     -- Date & time metadata
    tstamp,   -- ISO 8601 timestamp from EXIF
    -- Image metadata
    name,    -- Image name without the path
    hash,    -- Image hash
    iso,     -- ISO sensivity from EXIF
    exptime, -- exposure time in seconds from EXIF
    type,    -- LIGHT or DARK
    session -- session identifier
    FROM image_t
    '''
    cursor.execute(sql)
    return cursor


def read_old_sky(oldconn):
    cursor = oldconn.cursor()
    sql = '''
    SELECT hash, roi, 
    aver_signal_R1, vari_signal_R1,
    aver_signal_G2, vari_signal_G2,
    aver_signal_G3, vari_signal_G3,
    aver_signal_B4, vari_signal_B4
    FROM image_t
    '''
    cursor.execute(sql)
    return cursor


def createParser():
    # create the top-level parser
    name = os.path.split(os.path.dirname(sys.argv[0]))[-1]
    parser    = argparse.ArgumentParser(prog=name, description='AZOTEA MIGRATION TOOL')

    # Global options
    parser.add_argument('--version', action='version', version='{0} {1}'.format(name, __version__))
    parser.add_argument('-o', '--old', type=str, required=True, action='store', metavar='<file path>', help='Old SQLite database')
    parser.add_argument('-n', '--new', type=str, required=True, action='store', metavar='<file path>', help='New SQLite database')
    parser.add_argument('-nk','--no-console', action='store_true', help='Do not log to console.')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output.')
    parser.add_argument('-q', '--quiet',   action='store_true', help='Quiet output.')
    parser.add_argument('--log-file', type=str, default=None, help='Optional log file')
   
    return parser

def image_loop(oldconn, newconn):
    global save_list
    save_list = list()
    keys = ('family_name','surname','location_old','model','focal_length', 'f_number', 'display_name','tstamp','name','hash','iso','exptime','imagetype','session')
    for i, row in enumerate(read_old_image(oldconn), start=1):
        row = dict(zip(keys,row))
        row['observer_id'] = get_observer(newconn, row)
        row['location_id'] = get_location(newconn, row)
        row['camera_id']   = get_camera(newconn, row)
        row['date_id'], row['time_id'] = get_datetime(newconn, row)
        row['directory'] = '' # Unfortunately, we have lost this info in the old database
        row['flagged'] = 0
        row['gain']  = None
        save_list.append(row)
        if (i % BUFFER_SIZE) == 0:
            log.info(f"Saving to new database image {i} and {BUFFER_SIZE}  previous")
            #savemany_images(newconn, save_list)
            save_list = list()
    if(len(save_list) > 0):
        log.info(f"Saving to new database remaining images")
        #savemany_images(newconn, save_list)
        save_list = list()
    newconn.commit()


def sky_loop(oldconn, newconn):
    global save_list
    keys = ('hash', 'display_name', 
        'aver_signal_R','vari_signal_R',
        'aver_signal_G1', 'vari_signal_G1', 
        'aver_signal_G2', 'vari_signal_G2',
        'aver_signal_B', 'vari_signal_B',
    )
    save_list = list()
    for i, row in enumerate(read_old_sky(oldconn), start=1):
        row = dict(zip(keys,row))
        row['image_id']  = get_image_id_by_hash(newconn, row)
        row['roi_id']    = get_roi(newconn, row)
        row['published'] = 0
        save_list.append(row)
        if (i % BUFFER_SIZE) == 0:
            log.info(f"Saving to new database sky brightness {i} and {BUFFER_SIZE} previous")
            #savemany_sky(newconn, save_list)
            save_list = list()
    if(len(save_list) > 0):
        log.info(f"Saving to new database remaining sky brightness")
        #savemany_sky(newconn, save_list)
        save_list = list()
    newconn.commit()


def main():
    '''
    Utility entry point
    '''
    try:
        options = createParser().parse_args(sys.argv[1:])
        configureLogging(options)
        log.info("=============== AZOTEA NIGRATION TOOL{0} ===============".format(__version__))
        old = open_database(options.old)
        check_database(old, SQL_OLD_TEST)
        new = open_database(options.new)
        check_database(new, SQL_NEW_TEST)
        image_loop(old, new)
        sky_loop(old, new)
    except KeyboardInterrupt as e:
        log.critical("[%s] Interrupted by user ", __name__)
    except Exception as e:
        log.critical("[%s] Fatal error => %s", __name__, str(e) )
        traceback.print_exc()
    finally:
        pass

if __name__ == "__main__":
    main()