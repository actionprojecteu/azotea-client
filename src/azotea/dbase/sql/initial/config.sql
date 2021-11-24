--------------------------------------------------------
-- Miscelaneous data to be inserted at database creation
--------------------------------------------------------

-- Global section

INSERT INTO config_t(section, property, value) 
VALUES ( 'global', 'language', 'en');

INSERT INTO config_t(section, property, value) 
VALUES ('database', 'version', '01');

-- Default, persistent  settings

INSERT INTO config_t(section, property, value) 
VALUES ('observer', 'observer_id', NULL);

INSERT INTO config_t(section, property, value) 
VALUES ('location', 'location_id', NULL);

INSERT INTO config_t(section, property, value) 
VALUES ('camera', 'camera_id', NULL);

INSERT INTO config_t(section, property, value) 
VALUES ('ROI', 'roi_id', NULL);

-- Optics section

INSERT INTO config_t(section, property, value) 
VALUES ('optics', 'focal_length', NULL);

INSERT INTO config_t(section, property, value) 
VALUES ('optics', 'f_number', NULL);

-- Publishing section

INSERT INTO config_t(section, property, value) 
VALUES ('publishing', 'url', NULL);

INSERT INTO config_t(section, property, value) 
VALUES ('publishing', 'username', NULL);

INSERT INTO config_t(section, property, value) 
VALUES ('publishing', 'password', NULL);

INSERT INTO config_t(section, property, value) 
VALUES ('publishing', 'page_size', 100);

INSERT INTO config_t(section, property, value) 
VALUES ('publishing', 'tps', 1);

-- Logging processes section
-- the property names will be the logging namestaces

INSERT INTO config_t(section, property, value) 
VALUES ( 'logging', 'regis', 'info');
INSERT INTO config_t(section, property, value) 
VALUES ( 'logging', 'sky', 'info');
INSERT INTO config_t(section, property, value) 
VALUES ( 'logging', 'csv', 'info');
INSERT INTO config_t(section, property, value) 
VALUES ( 'logging', 'publ', 'info');


-- Per-table SQL Debugging
INSERT INTO config_t(section, property, value) 
VALUES ( 'tables', 'config_t', 'info');
INSERT INTO config_t(section, property, value) 
VALUES ( 'tables', 'observer_t', 'info');
INSERT INTO config_t(section, property, value) 
VALUES ( 'tables', 'location_t', 'info');
INSERT INTO config_t(section, property, value) 
VALUES ( 'tables', 'camera_t', 'info');
INSERT INTO config_t(section, property, value) 
VALUES ( 'tables', 'image_t', 'info');
INSERT INTO config_t(section, property, value) 
VALUES ( 'tables', 'roi_t', 'info');
INSERT INTO config_t(section, property, value) 
VALUES ( 'tables', 'sky_brightness_t', 'info');
