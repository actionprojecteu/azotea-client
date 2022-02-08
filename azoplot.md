# AZOPLOT

`azoplot` is a small utility for AZOTEA using [Python's matplotlib](https://matplotlib.org/) as a graphical backend. 
It works with RAW images taking by DSLR cameras and FITS images.

# Table of Contents

* [Usage](https://github.com/actionprojecteu/azotea-client/blob/main/azoplot.md#usage)
* [Use cases](https://github.com/actionprojecteu/azotea-client/blob/main/azoplot.md#use-cases)
    - [Bayer pattern layout](https://github.com/actionprojecteu/azotea-client/blob/main/azoplot.md#bayer-pattern-layout)
    - [Global bias estimation](https://github.com/actionprojecteu/azotea-client/blob/main/azoplot.md#global-bias-estimation)

# Usage

`azoplot` uses the same command line structure as `azotea` and `azotool`.

```
azpolot <global options> <command> <subcommand> <subcommand options>
```

where global options are:

* `--version`     Print program version and exit.
* `-h`  `--help`  Show program commands, subcommands and options.
* `-c`, `--console` Optionally logs to console. Needed for interactive use.
* `-l`, `--log file` Optional log file. Recommended for unattended use.

For a detailed view of all commands, subcommands and specific versions, please use the global `--help` option at every level.

***Note:*** Currently, the only command implemented is `image` and the only available subcommand is `stats`, which offer a series of default options:

```bash
azoplot --console image stats --help
usage: azoplot image stats [-h] (-d <path> | -f <path>) [-x WIDTH] [-y HEIGHT] [-b {RGGB,BGGR,GRBG,GBRG}]

optional arguments:
  -h, --help            show this help message and exit
  -d <path>, --images-dir <path>
                        Images directory
  -f <path>, --image-file <path>
                        single FITS file path
  -x WIDTH, --width WIDTH
                        Region of interest width [pixels].
  -y HEIGHT, --height HEIGHT
                        Region of interest height [pixels].
  -b {RGGB,BGGR,GRBG,GBRG}, --bayer {RGGB,BGGR,GRBG,GBRG}
                        Bayer pattern layout

```

When specified in the command line, the bayer pattern takes precedence over the bayer pattern information embedded in the image, if any.

## Examples



```bash
# This command plots a single image
azoplot -c image stats --images-dir ../images/Zamorano-Villaverde/FITS/202201/20220101-180045.10000.fits

# This command plots & cycles through all images in this directory
azoplot -c image stats --images-dir ../images/Zamorano-Villaverde/FITS/202201

```


# Use Cases

## Bayer pattern layout

EXIF cameras include the Bayer pattern layout of the underlying CMOS detector in the EXIF file. For FITS images, depending on the image capture software, this may not be the case. This bayer pattern can be guessed quite easily taking a RAW image pointing at the zenith during twilight, when the sky is still blue and examining the image file with `azoplot`. Both G channels should exhibit almost identical statistics. The B channel should have higher statistics than the red channel.


## Global Bias estimation

For AZOTEA sky background computation purposes, a simple global offset for all R, G, B channel is used. We wish to detect the bias added by the electronics & firmware. There is no need for separate channels bias nor spatial structural patterns detection, as performed by the standard astronomical images reduction pipeline procedures.

This global offset is automatically available in DSLR cameras as the black level per channel in the EXIF metadata. `azotea` uses only one figure. By examining several EXIF headers from different cameras, experience has shown us that this figure is a power of two and all channles show almost an exact power of two value.

For FITS images, depending on the image capture software, this information may not be available. You can use `azoplot` to examine a bias image taken with the minimun allowed exposure in you camera and a cover in front of your optics. `azoplot` shows all R, G1, G2, & B channels, draws a rectangle around the Region of Interest (OI) and computes the mean and stddev in this ROI.

Computed stats should be almost identical in all channels. Choose the one of your liking and set it as your global
`PEDESTAL` FITS keyword value in your FITS images. You can use `azofits` to include this information in all of your FITS images. See the [`azofits` documentation](https://github.com/actionprojecteu/azotea-client/blob/main/azofits.md)


