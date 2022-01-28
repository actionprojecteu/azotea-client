# FITS HEADERS FOR AZOTEA

Based on the popular *SharpCap* image capture software for astrocameras,
these are the additional FITS header keywords needed for AZOTEA:

* `SWCREATE`, Name of image capture software (i.e: SharpCap)
* `BAYERPAT`, Camera Bayer pattern (i.e. RGGB, GBRG, etc.)
* `INSTRUME`, Camera model (i.e )
* `DATE-OBS` Date time in ISO 8601 format (YYYY-MM-DDTHH:MM:SS)
* `ÈXPTIME`,  Exposure time *in seconds*
* `XPIXSZ`,  Pixel size in microns, width
* `YPIXSZ`,  Pixel size in microns, height

It would be also recommended to include:
* `IMAGETYP`, Image type (LIGHT, DARK, BIAS, FLAT)
* `LOG-GAIN` CMOS Camera Gain (i.e. 150)

Note that *SharpCap* do not include `IMAGETYP` and `LOG-GAIN` by default and
AZOTEA client software have some ad-hoc methods to derive the CMOS gain and image type.

## About the CMOS camera GAIN

The gain in ZWO cameras is expressed in a logaritmic scale gain with 0.1 dB units, that is:

```
LOG-GAIN = 100 * log10(G)
```

Where G is the internal amplifier gain of the analog circuitry.

Do not confuse this LOG-GAIN with the usual EGAIN, which is expressed in electrons/ADU.


## About BZERO & BSCALE

ZWO cameras usually employ a 16 bit unsigned integers to represent pixel values. 
However FITS do not support such data type, only 16 bit signed integers. 
The customary trick to handle this with the FITS reading software is by setting 
keywords BSCALE to 1 and BZERO to 32768.

## Bayer pattern issues

Depending on the application field (astronomy, general imaging), the images origin of coordinates (0,0) can either be top-left
or bottom-left. DSLR and generic imaging appliactons genearlly use the top-left convention. For FITS images, 
the custom from the 80s was to use a bottom-left origin.

The following CFA layout:

RGRGRG...RG
GBGBGB...BG

can be read as RGGB Bayer pattern, if using the top-left origin convention, or GBRG if using the bottom-up origin convention.

Azotea uses internally a top-left convention but SharpCap uses a bottom-left convention. 
So, the Bayer pattern 4 code letter in BAYERPAT keyword must be internally flipped to apply a correct debayering.


## Interesting links
[Interesting ClodyNights discussion](https://www.cloudynights.com/topic/692074-fits-keywords-bayerpat-bayoffx-bayoffy-etc/)

## FITS File Header Definitions

Diffraction Limited's Maxim DL software [compiled a series of FITS keyword definitions](https://cdn.diffractionlimited.com/help/maximdl/FITS_File_Header_Definitions.htm) for imaging and amateur observatoty neeeds. 
They are reproduced here, just in case the original page dissapears.

Mandatory FITS keywords are as follows:

```
    SIMPLE – always ”T”, indicating a FITS header.

    BITPIX – indicates array format. Options include unsigned 8-bit (8), signed 16 bit (16), signed 32 bit (32), 32-bit IEEE float (-32), and 64-bit IEEE float (-64). The standard format is 16; -64 can be read by MaxIm DL but is not written.

    NAXIS – number of axes in the data array. MaxIm DL uses 2 for monochrome images, and 3 for color images.

    NAXIS1 – corresponds to the X axis.

    NAXIS2 – corresponds to the Y axis.

    NAXIS3 – present only for color images; value is always 3 (red, green, blue color planes are present in that order).
```

Optional keywords defined by the FITS standard and used in MaxIm DL:

```
    BSCALE – this value should be multiplied by the data array values when reading the FITS file. MaxIm DL always writes a value of 1 for this keyword.

    BZERO – this value should be added to the data array values when reading the FITS file. For 16-bit integer files, MaxIm DL writes 32768 (unless overridden by the Settings dialog).

    DATE-OBS – date of observation in the ISO standard 8601 format (Y2K compliant FITS): CCYY-MM-DDThh:mm:ss.sss. The Universal time at the start of the exposure is used. Note: the alternate format using DATE-OBS and TIME-OBS is not written, but MaxIm DL will correctly interpret it when read. The time is written to 10 ms resolution. The default behavior is to report the start of observation time, but individual camera drivers can change this.  As of Version 6.24 the DL Imaging driver sets the time to exposure midpoint.  

    HISTORY – indicates the processing history of the image. This keyword may be repeated as many times as necessary.

    INSTRUME – camera information. Either user entered or obtained from the camera driver.

    OBJECT – name or catalog number of object being imaged, if available from Observatory Control window or specified by the user in Settings.

    OBSERVER – user-entered information; the observer’s name.

    TELESCOP – user-entered information about the telescope used.
```

Extension keywords that may be added or read by MaxIm DL, depending on the current equipment and software configuration:

```
    AIRMASS – relative optical path length through atmosphere.

    AOCAMBT – ASCOM Observatory Conditions – Ambient temperature in degrees C

    AOCDEW – ASCOM Observatory Conditions – Dew point in degrees C

    AOCRAIN – ASCOM Observatory Conditions – Rain rate in mm/hour

    AOCHUM – ASCOM Observatory Conditions – Humidity in percent

    AOCWIND – ASCOM Observatory Conditions – Wind speed in m/s

    AOCWINDD – ASCOM Observatory Conditions – Wind direction in degrees (0..360)

    AOCWINDG – ASCOM Observatory Conditions – Wind gust in m/s

    AOCBAROM – ASCOM Observatory Conditions – Barometric pressure in hPa

    AOCCLOUD – ASCOM Observatory Conditions – Cloud coverage in percent

    AOCSKYBR – ASCOM Observatory Conditions – Sky brightness in Lux

    AOCSKYQU – ASCOM Observatory Conditions – Sky quality (magnitudes per square arcsecond)

    AOCSKYT – ASCOM Observatory Conditions – Sky temperature in degrees C

    AOCFWHM – ASCOM Observatory Conditions – Seeing FWHM in arc seconds

    APTDIA – diameter of the telescope in millimeters.

    APTAREA – aperture area of the telescope in square millimeters. This value includes the effect of the central obstruction.

    BAYERPAT – if present the image has a valid Bayer color pattern.

    BOLTAMBT – Boltwood Cloud Sensor ambient temperature in degrees C.

    BOLTCLOU – Boltwood Cloud Sensor cloud condition.

    BOLTDAY – Boltwood Cloud Sensor daylight level.

    BOLTDEW – Boltwood Cloud Sensor dewpoint in degrees C.

    BOLTHUM – Boltwood Cloud Sensor humidity in percent.

    BOLTRAIN – Boltwood Cloud Sensor rain condition.

    BOLTSKYT – Boltwood Cloud Sensor sky minus ambient temperature in degrees C.

    BOLTWIND – Boltwood Cloud Sensor wind speed in km/h.

    CALSTAT – indicates calibration state of the image; B indicates bias corrected, D indicates dark corrected, F indicates flat corrected.

    CENTAZ – nominal Azimuth of center of image in degrees.

    CENTALT – nominal Altitude of center of image in degress.

    CBLACK – indicates the black point used when displaying the image (screen stretch).

    CSTRETCH – initial display screen stretch mode.

    CCD-TEMP – actual measured sensor temperature at the start of exposure in degrees C. Absent if temperature is not available.

    COLORTYP – type of color sensor Bayer array or zero for monochrome.

    CWHITE – indicates the white point used when displaying the image (screen stretch).

    DATAMAX – pixel values above this level are considered saturated.

    DAVRAD – Davis Instruments Weather Station solar radiation in W/m^2

    DAVRAIN – Davis Instruments Weather Station accumulated rainfall in mm/day

    DAVAMBT – Davis Instruments Weather Station ambient temperature in deg C

    DAVDEW – Davis Instruments Weather Station dewpoint in deg C

    DAVHUM – Davis Instruments Weather Station humidity in percent

    DAVWIND – Davis Instruments Weather Station wind speed in km/h

    DAVWINDD – Davis Instruments Weather Station wind direction in deg

    DAVBAROM – Davis Instruments Weather Station barometric pressure in hPa

    EXPTIME – duration of exposure in seconds.

    DARKTIME – dark current integration time, if recorded. May be longer than exposure time.

    EGAIN – electronic gain in photoelectrons per ADU.

    FILTER – name of selected filter, if filter wheel is connected.

    FLIPSTAT – status of pier flip for German Equatorial mounts.

    FOCALLEN – focal length of the telescope in millimeters.

    FOCUSPOS – Focuser position in steps, if focuser is connected.

    FOCUSSSZ – Focuser step size in microns, if available.

    FOCUSTEM – Focuser temperature readout in degrees C, if available.

    IMAGETYP – type of image: Light Frame, Bias Frame, Dark Frame, Flat Frame, or Tricolor Image.

    INPUTFMT – format of file from which image was read.

    ISOSPEED – ISO camera setting, if camera uses ISO speeds.

    JD or JD_GEO – records the geocentric Julian Day of the start of exposure.

    JD-HELIO or JD_HELIO – records the Heliocentric Julian Date at the exposure midpoint.

    MIDPOINT – UT of midpoint of exposure.

    NOTES – user-entered information; free-form notes.

    OBJECT – name or designation of object being imaged.

    OBJCTALT – nominal altitude of center of image             

    OBJCTAZ – nominal azimuth of center of image

    OBJCTDEC – Declination of object being imaged, string format DD MM SS, if available. Note: this is an approximate field center value only.

    OBJCTHA – nominal hour angle of center of image

    OBJCTRA – Right Ascension of object being imaged, string format HH MM SS, if available. Note: this is an approximate field center value only.

    PEDESTAL – add this value to each pixel value to get a zero-based ADU. Calibration in MaxIm DL sets this to 100.

    PIERSIDE – indicates side-of-pier status when connected to a German Equatorial mount.

    READOUTM – records the selected Readout Mode (if any) for the camera.

    ROTATANG – Rotator angle in degrees, if focal plane rotator is connected.

    ROWORDER – Images taken by MaxIm DL are always TOP-DOWN.  

    SBSTDVER – string indicating the version of the SBIG FITS extensions supported.

    SET-TEMP – CCD temperature setpoint in degrees C. Absent if setpoint was not entered.

    SITELAT – latitude of the imaging site in degrees, if available. Uses the same format as OBJECTDEC.

    SITELONG – longitude of the imaging site in degrees, if available. Uses the same format as OBJECTDEC.

    SNAPSHOT – number of images combined.

    SWCREATE – string indicating the software used to create the file; will be ”MaxIm DL Version x.xx”, where x.xx is the current version number.

    SWMODIFY – string indicating the software that modified the file. May be multiple copies.

    TILEXY – indicates tile position within a mosaic.

    TRAKTIME – exposure time of the autoguider used during imaging.

    XBAYROFF – X offset of Bayer array on imaging sensor.

    YBAYROFF – Y offset of Bayer array on imaging sensor.

    XBINNING – binning factor used on X axis

    XORGSUBF – subframe origin on X axis

    XPIXSZ – physical X dimension of the sensor's pixels in microns (present only if the information is provided by the camera driver). Includes binning.

    YBINNING – binning factor used on Y axis

    YORGSUBF – subframe origin on Y axis

    YPIXSZ – physical Y dimension of the sensor's pixels in microns (present only if the information is provided by the camera driver). Includes binning.
```
