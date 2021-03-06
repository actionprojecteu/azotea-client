-------------------------------
-- azotea database Data Model
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
    longitude       REAL,             -- Longitude in decimal degrees
    latitude        REAL,             -- Latitude in decimal degrees
    randomized      INTEGER,          -- Coordinates are randomized
    utc_offset      REAL,             -- time zone as offset from UTC. i.e. GMT+1 = +1
    UNIQUE(site_name,location),
    PRIMARY KEY(location_id)
);

CREATE TABLE IF NOT EXISTS camera_t
(
    camera_id           INTEGER,
    model               TEXT,         -- Camera Model (taken from EXIF data or FITS header)
    bias                INTEGER,      -- default bias, to be replicated in all channels if we cannot read it from EXIF
    extension           TEXT,         -- File extension procuced by a camera (i.e. *.NEF)
    header_type         TEXT,         -- Either 'EXIF' or 'FITS'
    bayer_pattern       TEXT,         -- Either "RGGB", "BGGR", "GRBG" , "GBGR"
    width               INTEGER DEFAULT 0, -- Number of raw columns, without debayering
    length              INTEGER DEFAULT 0, -- Number of raw rows, without debayering
    x_pixsize           REAL,         -- pixel size in microns (width)
    y_pixsize           REAL,         -- pixel size in microns (height)
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
    display_name     TEXT,     -- as NumPy region text, ie. [y1:y2,x1:x2]
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
    imagetype           TEXT,              -- Either 'LIGHT' or 'DARK'
    flagged             INTEGER,           -- 0 = image is ok, 1 = flagged as corrupt image

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
    -- References to dimensions/parent table
    image_id            INTEGER NOT NULL,
    roi_id              INTEGER NOT NULL,
    -- Sky Brightness Measurements
    aver_signal_R      REAL,             -- R raw signal mean without dark substraction
    vari_signal_R      REAL,             -- R raw signal variance without dark substraction 
    aver_signal_G1     REAL,             -- G1 raw signal mean without dark substraction
    vari_signal_G1     REAL,             -- G1 raw signal variance without dark substraction
    aver_signal_G2     REAL,             -- G2 raw signal mean without dark substraction
    vari_signal_G2     REAL,             -- G2 raw signal variance without dark substraction
    aver_signal_B      REAL,             -- B raw signal mean without dark substraction
    vari_signal_B      REAL,             -- B raw signal variance without dark substraction
    -- Management
    published         INTEGER DEFAULT 0, -- Published in server flag

    FOREIGN KEY(image_id)    REFERENCES image_t(image_id),
    FOREIGN KEY(roi_id)      REFERENCES roi_t(roi_id),
    PRIMARY KEY(image_id, roi_id)
);

-------------------------------------------------------------------
-- This view is needed to perform exports including the ROI details
-- not present in the image_t table
--------------------------------------------------------------------

CREATE VIEW IF NOT EXISTS sky_brightness_v
AS SELECT
    s.image_id,
    -- ROI details
    r.x1,
    r.y1,
    r.x2,
    r.y2,
    r.display_name,
    r.comment,
    -- Sky Brighntess Measurements
    s.aver_signal_R , 
    s.vari_signal_R, 
    s.aver_signal_G1, 
    s.vari_signal_G1, 
    s.aver_signal_G2, 
    s.vari_signal_G2, 
    s.aver_signal_B, 
    s.vari_signal_B, 
    -- Management
    s.published,
    -- Derived fields
    (r.y2 - r.y1) AS height,
    (r.x2 - r.x1) AS width
FROM sky_brightness_t AS s
JOIN roi_t AS r USING(roi_id);
