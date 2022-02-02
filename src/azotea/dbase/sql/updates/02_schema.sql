------------------------------------------------------
-- Miscelanea data to be inserted at database creation
------------------------------------------------------

PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;

-- ----------------------
-- Schema version upgrade
-- ----------------------

ALTER TABLE camera_t ADD COLUMN x_pixsize REAL;
ALTER TABLE camera_t ADD COLUMN y_pixsize REAL;

INSERT OR REPLACE INTO config_t(section, property, value) 
VALUES ('database', 'version', '02');


COMMIT;
