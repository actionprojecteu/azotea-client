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
* `IMAGETYP`, Image type (LIGHT, DARK, BIAS, FLAT)
* `LOG-GAIN` CMOS Camera Gain (i.e. 150)

Note that *SharpCap* do not include `IMAGETYP` and `LOG-GAIN` by default and
AZOTEA client software have some ad-hoc methods to derive the CMOS gain and image type.

## About the CMOS camera GAIN

The GAIN in ZWO cameras is expressed in a logaritmic scale gain with 0.1 dB units, that is:

```
LOG-GAIN = 100 * log10(G)
```

Where G is the internal gain of the analog circuitry.

## About BZERO & BSCALE

ZWO cameras usually employ a 16 bit unsigned integers to represent pixel values. 
However FITS do not support such data type, only 16 bit signed integers. 
The customary trick to handle this with the FITS reading software is by setting 
keywords BSCALE to 1 and BZERO to 32768.
