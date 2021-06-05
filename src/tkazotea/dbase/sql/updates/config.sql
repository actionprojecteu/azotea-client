--------------------------------------------------------
-- Miscelaneous data to be inserted at database creation
--------------------------------------------------------

PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;

-- -------------
-- SQL infoging
-- -------------

-- Per-table SQL Debugging
INSERT OR REPLACE INTO config_t(section, property, value) 
VALUES ( 'tables', 'config_t', 'info');
INSERT OR REPLACE INTO config_t(section, property, value) 
VALUES ( 'tables', 'observer_t', 'info');
INSERT OR REPLACE INTO config_t(section, property, value) 
VALUES ( 'tables', 'location_t', 'info');
INSERT OR REPLACE INTO config_t(section, property, value) 
VALUES ( 'tables', 'camera_t', 'info');
INSERT OR REPLACE INTO config_t(section, property, value) 
VALUES ( 'tables', 'image_t', 'info');
INSERT OR REPLACE INTO config_t(section, property, value) 
VALUES ( 'tables', 'roi_t', 'info');
INSERT OR REPLACE INTO config_t(section, property, value) 
VALUES ( 'tables', 'sky_brightness_t', 'info');

COMMIT;
