# AZOFITS

`azofits` is a ***FITS HEADER batch editor for AZOTEA*** entirely written in Python.
It is tuned to the FITS keywords that `azotea` processing pipeline needs.

FITS is a very flexible file frmat for astronomical images and very few keywords
have been standarized. Amateur astroimaging software flourished in the 90s
and some FITS keywords proposals were made for interoperatbility for ASCOM programs.

Diffraction Limited's Maxim DL software [compiled a series of FITS keyword definitions](https://cdn.diffractionlimited.com/help/maximdl/FITS_File_Header_Definitions.htm) for imaging and amateur observatoty neeeds. 
Whenever possible, `azotea` reuses these keywords.

CCD/CMOS image adquistion software already produces images in FITS format, either for B&W images or RAW color images.
Each image adquistion software has its own convention and idiosyncrasies, so `azofits` was written to cope with this and supply trouble-free FITS images to `azotea`.

# Table of Contents

* [AZOTEA FITS keywords](https://github.com/actionprojecteu/azotea-client/blob/main/azofits.md#azoteaa-fits-keywords)
* [Usage](https://github.com/actionprojecteu/azotea-client/blob/main/azofits.md#usage)
    - [Examples](https://github.com/actionprojecteu/azotea-client/blob/main/azofits.md#examples)
* [Miscelanea](https://github.com/actionprojecteu/azotea-client/blob/main/azofits.md#miscelanea)


# AZOTEA FITS keywords

| Header   | Units | Description | Notes
|:--------:| :---: | ----------- | -------
|`SWCREATE`|       | Image capture software (i.e: `SharpCap`).
|`SWMODIFY`|       | Image editing sofware (always `azofits`).
|`BAYERPAT`|       | Camera Bayer pattern (`RGGB`, `BGGR`, `GRBG`, `GBRG`). | See [Note 1](https://github.com/actionprojecteu/azotea-client/blob/main/azofits.md#note-1)
|`INSTRUME`|       | Camera model (i.e. `ZWO ASI178MC`).
|`DATE-OBS`|       | Date time in ISO 8601 format | See [Note 2](https://github.com/actionprojecteu/azotea-client/blob/main/azofits.md#note-2).
|`ÈXPTIME` | sec.  | Exposure time.
|`PEDESTAL`| ADUs  | Global electronic bias. Same for all channels.
|`FOCALLEN`| mm.   | Focal length.
|`APTDIA`  | mm.   | Aperture diameter.
|`XPIXSZ`  | um.   | Horizontal pixel size.
|`YPIXSZ`  | um.   | Vertical pixel size.
|`LOG-GAIN`| 0.1 dB| Logaritmic gain. | See [Note 3](https://github.com/actionprojecteu/azotea-client/blob/main/azofits.md#note-3).
|`IMAGETYP`|       | Image type | See [Note 4](https://github.com/actionprojecteu/azotea-client/blob/main/azofits.md#note-3).

## Note 1:

Depending on the application field (astronomy, general imaging), the images origin of coordinates (0,0) can either be top-down or bottom-up.For FITS images, the custom from the 80s was to read pixels use a bottom-up origin. `azotea` uses the top-down origin convention.

The following CFA layout can be read as `RGGB` Bayer pattern if using the top-down origin convention or `GBRG` if using the bottom-up origin convention, as shown below:

```
                      (0,0)
     +---+---+          +---+---+         +---+---+
     | R | G |          | R | G |         | R | G |
     +---+---+   =>     +---+---+    or   +---+---+
     | G | B |          | G | B |         | G | B |
     +---+---+          +---+---+         +---+---+
                                        (0,0)   
```


`azotea` uses internally a top-down convention but SharpCap uses a bottom-up convention. 
So, for some FITS writers like *SharpCap*, the Bayer pattern 4 code letter in BAYERPAT keyword must be flipped to apply a correct debayering in `azotea`.

## Note 2:
`azofits` allows both `YYYY-MM-DDTHH:MM:SS` or `YYYY-MM-DDTHH:MM:SS.fffff`  with up to 6 seconds decimals.

## Note 3:
The gain in ZWO cameras is expressed in a logaritmic scale gain with 0.1 dB units, that is:
```
LOG-GAIN = 100 * log10(G)
```
Where `G` is the internal amplifier gain of the analog circuitry.
This is a new keyword, not present in the [Maxim DL FITS specification](https://cdn.diffractionlimited.com/help/maximdl/FITS_File_Header_Definitions.htm) and 
not to be confused  with the `EGAIN` keyword which specifies a "gain" (conversion factor) in e-/ADU.

## Note 4:
[Maxim DL FITS specifications](https://cdn.diffractionlimited.com/help/maximdl/FITS_File_Header_Definitions.htm) list as values for this keyword the following strings:
* `Light Frame` for monocrome images
* `Tricolor Image` for images taken by RGB color cameras
* `Bias Frame`
* `Dark Frame` 
* `Flat Frame`

# Usage

The `azofits` executable has the same structure:

```
azofits  <options>
```
Type `azofits --help` to see the complete list of options.

## General behaviour

* All FITS edition options are optional. However, if passed, they will take precedence over values already present in the appropiate FITS keyword and will be overwritten or created if they didn't exist.
* A `HISTORY` keyword will be added describing each keyword change.
* Once the FITS image is edited and `SWMODIFY` (=`azofits`) is added, no further edition is possible (*Exception: --force option*)


## generic options

* `--version`     Print program version and exit.
* `-h`  `--help`  Show program commands, subcommands and options.
* `-c`, `--console` Optionally logs to console. Needed for interactive use.
* `-l`, `--log file` Optional log file. Recommended for unattended use.
* `-q`, `--quiet` Optional less verbose output.

## FITS editing options

* `--images-dir`.   Base directory for multi-file edition. Mutually exclusive to `--image-file`
* `--image-file`.   Single FITS file edition. Mutually exclusive to `--images-dir`
* `--swcreator`.    Specifies a software creator if not present in the FITS image (`SWCREATE`)
* `--camera`.       Sets the camera model (`INSTRUME`).
* `--bayer-pattern` Sets the bayer pattern model (`BAYERPAT`).
* `--gain`          CMOS detector GAIN settings (`LOG-GAIN`)
* `--bias`          Global pedestal value for all channels [ADU]  (`PEDESTAL`)
* `--x-pixsize`     Pixel size, width [um]   (`XPIXSZ`)
* `--y-pixsize`     Pixel size, height [um]  (`YPIXSZ`)
* `--exptime`       Image exposure time [s]  (`EXPTIME`)
* `--focal-length`  Optics focal length [mm]  (`FOCALLEN`)
* `--diameter`      Optics diameter [mm]  (`APTDIA`)
* `--image-type`    Image type  (`IMAGETYP`)

## Examples

### SharpCap FITS images

SharpCap FITS images have a few issues that are edited/corrected by `azofits`:
* It uses the older `BAYEROFX`, `BAYOFFY` keywords, which are substituted by `XBAYROFF`, `YBAYROFF`
* `DATE-OBS` timestamp have seconds with excess decimals, so the timestamp is fixed.
* `BAYERPAT` uses a bottom-up pattern convention, so the 4-letter pattern code is flipped.
* CMOS camera gain keyword is not included in the FITS file. However, it is included in a separate
metadata XXXX_CameraSettings.txt file for each XXXX.fits image. To  properly include the CMOS GAIN, `azofits` needs this additional metadata file alongside with the FITS file.

Fortunately, SharpCap FITS images already include `SWCREATE` so they can be properly detected and there is no need
to specify it in the command line.

The command line is shown below:

```bash
azofits --console --images-dir ../images/Zamorano-Villaverde-del-Ducado/FITS --bias 64 --diameter 10 --focal-length 35 
```

*Note: values are just ficticuous examples*

We specify a default optics configuration, as the FITS headers did not include this information

### captura-fits FITS images

This image adquistion software, developed by Alberto Castellon, is used in meteor & fireball detection. It includes a minimalistic FITS keyword set and encodes the observation date & exposure time in the file name as `yyyy-mm-dd.exptime.fits`
where the exposure time is given in milliseconds. `azofits` handle this case too

The command line is shown below:

```bash
azofits --console --images-dir ../images/Zamorano-Villaverde-del-Ducado/FITS --swcreator captura-fits --camera ZWO ASI178MC --bayer-pattern RGGB --gain 150 --bias 64 --diameter 10 --focal-length 35
```
*Note: values are just ficticuous examples*

Note that, except for the timestamp and exposition time, we have to specify almost everything, even the software creation tag, which also flags `azofits` to forward thos edition to the appropiate internal "capturafits driver"

## Using `azofits` ,with `azotool` & `azotea`

Note that `azofits` must *always* be used before invoking `azotea`.
Once FITS images are pre-procesed by `azofits`, camera and ROI metadata creation in the AZOTEA database creation can be 
made from FITS images, as shown in the example below.

```bash
# Edit FITS headers with AZOFITS
# Assume that IMAGES & DBASE variables have been set at the beginning of the script
azofits --console --images-dir ${IMAGES}/202201 --swcreator captura-fits --camera ZWO ASI178MC --bayer-pattern RGGB --gain 150 --bias 64 --diameter 10 --focal-length 35

# Input metadata with AZOTOOL
# Assume that observer & location metadata has already been input
azotool --console --dbase ${DBASE} camera create --default \
        --from-image ${IMAGES}/202201/20220101-183017.10000.fits

azotool --console --dbase ${DBASE} roi create --default --width 500 --height 400 \
        --from-image ${IMAGES}/202201/20220101-183017.10000.fits

# Load images in AZOTEA database and compute statistics
azotea --console --dbase ${DBASE} --images-dir ${IMAGES}/202201
```

# Miscelanea

## Interesting links
[Interesting ClodyNights discussion](https://www.cloudynights.com/topic/692074-fits-keywords-bayerpat-bayoffx-bayoffy-etc/)

## FITS File Header Definitions

Copy of [Maxim DL FITS specifications](https://cdn.diffractionlimited.com/help/maximdl/FITS_File_Header_Definitions.htm)

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
