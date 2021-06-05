-------------------------------
-- TKAzotea database Data Model
-------------------------------

-- This is the database counterpart of a configuration file
-- All configurations are stored here
CREATE TABLE IF NOT EXISTS config_t
(
    section        TEXT,  -- Configuration section
    property       TEXT,  -- Property name
    value          TEXT,  -- Property value
    PRIMARY KEY(section, property)
);


CREATE TABLE IF NOT EXISTS date_t
(
    date_id        INTEGER, 
    sql_date       TEXT,    -- Date as a YYYY-MM-DD string
    date           TEXT,    -- date as a Spanish date string DD-MM-YYYY
    day            INTEGER, -- day within month (1 .. 31)
    day_year       INTEGER, -- day within the year 1..366
    julian_day     REAL,    -- day as Julian Day, at 00:00 UTC
    weekday        TEXT,    -- Monday, Tuesday, ...
    weekday_abbr   TEXT,    -- Abbreviated weekday: Mon, Tue, ...
    weekday_num    INTEGER, -- weekday as number 0=Sunday
    month_num      INTEGER, -- month as number: Jan=1, Feb=2, ..
    month          TEXT,    -- January, February, ...
    month_abbr     TEXT,    -- Jan, Feb, ...
    year           INTEGER, -- Year (2000, 2001, ...)
    PRIMARY KEY(date_id)
);


CREATE TABLE IF NOT EXISTS time_t
(
    time_id        INTEGER, 
    time           TEXT,    -- Time as HH:MM;SS string, 24 hour format
    hour           INTEGER, -- hour 00-23
    minute         INTEGER, -- minute 00-59
    second         INTEGER, -- second 00-59
    day_fraction   REAL,    -- time as a day fraction between 0 and 1
    PRIMARY KEY(time_id)
);


CREATE TABLE IF NOT EXISTS observer_t
(
    observer_id     INTEGER,
    family_name     TEXT,             -- Observer family name (used only for dataset Zenodo publication)
    surname         TEXT,             -- Observer surname (used only for dataset Zenodo publication)
    affiliation     TEXT,             -- Observer affiliation (i.e. Agrupacion Astronomica de Madrid)
    acronym         TEXT,             -- Affiliation acronym (i.e. AAM)
    valid_since     TEXT,
    valid_until     TEXT,
    valid_state     TEXT,              -- Either 'Current' or 'Expired'
    UNIQUE(family_name,surname,affiliation,acronym,valid_since,valid_until)
    PRIMARY KEY(observer_id)
);

CREATE TABLE IF NOT EXISTS location_t
(
    location_id     INTEGER,
    site_name       TEXT,             -- name identifying the site
    location        TEXT,             -- City/Town where the site belongs to
    longitude       REAL,             -- True longitude in decimal degrees
    latitude        REAL,             -- True latitude in decimal degrees
    public_long     REAL,             -- Public, randomized longitude in decimal degrees
    public_lat      REAL,             -- Public, randomized latitude in decimal degrees
    utc_offset      REAL,             -- time zone as offset from UTC. i.e. GMT+1 = +1
    UNIQUE(site_name,location),
    PRIMARY KEY(location_id)
);

CREATE TABLE IF NOT EXISTS camera_t
(
    camera_id           INTEGER,
    model               TEXT,         -- Camera Model (taken from EXIF data)
    bias                INTEGER,      -- default bias, to be replicated in all channels if we canno read ir from EXIR
    extension           TEXT,         -- File extension procuced by a camera (i.e. *.NEF)
    header_type         TEXT,         -- Either 'EXIF' or 'FITS'
    bayer_pattern       TEXT,         -- Either "RGGB", "BGGR", "GRGB" , "GBGR"
    width               INTEGER DEFAULT 0, -- Number of raw columns, without debayering
    length              INTEGER DEFAULT 0, -- Number of raw rows, without debayering
    UNIQUE(model),
    PRIMARY KEY(camera_id)
);

-- Region of Interest (ROI)
CREATE TABLE IF NOT EXISTS roi_t
(
    roi_id           INTEGER,
    x1               INTEGER,     -- x1 should be x1 <= x2         
    y1               INTEGER,     -- y1 should be y1 <= x2
    x2               INTEGER,
    y2               INTEGER,
    display_name     TEXT,
    comment          TEXT,     -- Descriptive comment
    UNIQUE(x1,y1,x2,y2),
    PRIMARY KEY(roi_id)
);

CREATE TABLE IF NOT EXISTS image_t
(
    image_id            INTEGER,
    name                TEXT NOT NULL,     -- Image name without the path
    directory           TEXT NOT NULL,     -- Directory path
    hash                BLOB  UNIQUE,      -- Image hash (alternative key in fact)
    
    iso                 TEXT,              -- DSLR ISO sensivity from EXIF
    gain                REAL,              -- For imagers that do not have ISO (i.e CMOS astrocameras saving in FITS)
    exptime             REAL,              -- exposure time in seconds from EXIF
    focal_length        REAL,              -- Either from configuration or EXIF
    f_number            REAL,              -- Either from configuration or EXIF

    session             INTEGER NOT NULL,  -- session identifier
    date_id             INTEGER NOT NULL,  -- decoded from tstamp & cached for later insert in in sky brightness table
    time_id             INTEGER NOT NULL,  -- decoded from tstamp & cached for later insert in in sky brightness table
    camera_id           INTEGER NOT NULL,  -- From EXIF lookup   
    location_id         INTEGER NOT NULL,  -- From default observer
    observer_id         INTEGER NOT NULL,  -- From default location

    FOREIGN KEY(date_id)     REFERENCES date_t(date_id),
    FOREIGN KEY(time_id)     REFERENCES time_t(time_id),
    FOREIGN KEY(camera_id)   REFERENCES camera_t(camera_id),
    FOREIGN KEY(location_id) REFERENCES location_t(location_id),
    FOREIGN KEY(observer_id) REFERENCES observer_t(observer_id),
    PRIMARY KEY(image_id)
);

CREATE TABLE IF NOT EXISTS sky_brightness_t
(
    -- References to dimensions
    observer_id         INTEGER NOT NULL,
    location_id         INTEGER NOT NULL,
    camera_id           INTEGER NOT NULL,
    image_id            INTEGER NOT NULL,
    roi_id              INTEGER NOT NULL,
    date_id             INTEGER NOT NULL,
    time_id             INTEGER NOT NULL,

    -- Sky Brighntess Measurements
    aver_signal_R      REAL,             -- R raw signal mean without dark substraction
    vari_signal_R      REAL,             -- R raw signal variance without dark substraction
    aver_dark_R        REAL DEFAULT 0.0, -- R dark level R1 either from master dark or dark_roi
    vari_dark_R        REAL DEFAULT 0.0, -- R dark variance either from master dark or dark_roi

    aver_signal_G1      REAL,             -- G1 raw signal mean without dark substraction
    vari_signal_G1      REAL,             -- G1 raw signal variance without dark substraction
    aver_dark_G1        REAL DEFAULT 0.0, -- G1 dark level either from master dark or dark_roi
    vari_dark_G1        REAL DEFAULT 0.0, -- G1 dark variance either from master dark or dark_roi

    aver_signal_G2      REAL,             -- G2 raw signal mean without dark substraction
    vari_signal_G2      REAL,             -- G2 raw signal variance without dark substraction
    aver_dark_G2        REAL DEFAULT 0.0, -- G2 dark level either from master dark or dark_roi
    vari_dark_G2        REAL DEFAULT 0.0, -- G2 dark variance either from master dark or dark_roi

    aver_signal_B      REAL,             -- B raw signal mean without dark substraction
    vari_signal_B      REAL,             -- B raw signal variance without dark substraction
    aver_dark_B        REAL DEFAULT 0.0, -- B dark level either master dark or dark_roi
    vari_dark_B        REAL DEFAULT 0.0, -- B dark variance either master dark or dark_roi

    -- Management
    published         INTEGER DEFAULT 0, -- Published in server flag

    FOREIGN KEY(date_id)     REFERENCES date_t(date_id),
    FOREIGN KEY(time_id)     REFERENCES time_t(time_id),
    FOREIGN KEY(camera_id)   REFERENCES camera_t(camera_id),
    FOREIGN KEY(location_id) REFERENCES location_t(location_id),
    FOREIGN KEY(observer_id) REFERENCES observer_t(observer_id),
    FOREIGN KEY(roi_id)      REFERENCES roi_t(roi_id),
    PRIMARY KEY(image_id,roi_id)
);



CREATE TABLE IF NOT EXISTS master_dark_t
(
    session             INTEGER,             -- session id
    aver_R1             REAL    NOT NULL,    -- Red mean dark level
    vari_R1             REAL    NOT NULL,    -- Red dark vari
    aver_G1             REAL    NOT NULL,    -- Green 1 mean dark level
    vari_G1             REAL    NOT NULL,    -- Green 1 dark variance
    aver_G2             REAL    NOT NULL,    -- Green 2 mean dark level
    vari_G2             REAL    NOT NULL,    -- Green 2 dark variance
    aver_B              REAL    NOT NULL,    -- Blue mean dark level
    vari_B              REAL    NOT NULL,    -- Blue dark variance
    min_exptime         REAL    NOT NULL,    -- Minimun session exposure time
    max_exptime         REAL    NOT NULL,    -- Maximun session exposure time
    roi_id              INTEGER NOT NULL,    -- region of interest
    N                   INTEGER NOT NULL,    -- number of darks used to average
    FOREIGN KEY(roi_id) REFERENCES roi_t(roi_id),
    PRIMARY KEY(session)
);
