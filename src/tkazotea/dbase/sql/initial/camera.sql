--------------------------------------------------------
-- Miscelaneous data to be inserted at database creation
--------------------------------------------------------

BEGIN TRANSACTION;
-- ------------
-- CANON Models
-- ------------

INSERT INTO camera_t(model, header_type, bayer_pattern, bias, extension) 
VALUES ('Canon EOS 200D', 'EXIF', 'RGGB', 2048, '.CR2');

INSERT INTO camera_t(model, header_type, bayer_pattern, bias, extension) 
VALUES ('Canon EOS 400D DIGITAL', 'EXIF', 'RGGB', 256, '.CR2');

INSERT INTO camera_t(model, header_type, bayer_pattern, bias, extension) 
VALUES ('Canon EOS 450D', 'EXIF', 'RGGB', 1024, '.CR2');

INSERT INTO camera_t(model, header_type, bayer_pattern, bias, extension) 
VALUES ('Canon EOS 550D', 'EXIF', 'GBRG', 2048, '.CR2');

INSERT INTO camera_t(model, header_type, bayer_pattern, bias, extension) 
VALUES ('Canon EOS 750D', 'EXIF', 'RGGB', 2048, '.CR2');

INSERT INTO camera_t(model, header_type, bayer_pattern, bias, extension) 
VALUES ('Canon EOS 1300D', 'EXIF', 'GRBG', 2048, '.CR2');

-- REVIEW BIAS AND EXTENSION !!!!!!!! ...
INSERT INTO camera_t(model, header_type, bayer_pattern, bias, extension) 
VALUES ('Canon EOS 77D', 'EXIF', 'RGGB', 0, '.CR2');

-- ------------
-- Nikon Models
-- ------------

INSERT INTO camera_t(model, header_type, bayer_pattern, bias, extension) 
VALUES ('NIKON D5200', 'EXIF', 'RGGB', 0, '.NEF');

INSERT INTO camera_t(model, header_type, bayer_pattern, bias, extension) 
VALUES ('NIKON 1 V1', 'EXIF', 'RGGB', 0, '.NEF');

INSERT INTO camera_t(model, header_type, bayer_pattern, bias, extension) 
VALUES ('NIKON D50', 'EXIF', 'BGGR', 0, '.NEF');

-- --------------
-- Olympus Models
-- --------------

INSERT INTO camera_t(model, header_type, bayer_pattern, bias, extension) 
VALUES ('E-M10', 'EXIF', 'RGGB', 256, '.ORF');

-- --------------
-- Pentax Models
-- --------------

INSERT INTO camera_t(model, header_type, bayer_pattern, bias, extension) 
VALUES ('PENTAX K100D Super', 'EXIF', 'RGGB', 128, '.PEF');

COMMIT;
