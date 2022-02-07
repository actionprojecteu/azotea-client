# ----------------------------------------------------------------------
# Copyright (c) 2020
#
# See the LICENSE file for details
# see the AUTHORS file for authors
# ----------------------------------------------------------------------

#--------------------
# System wide imports
# -------------------

import os
import glob
import logging
import traceback

# -------------------
# Third party imports
# -------------------

import exifread
import rawpy
from astropy.io import fits

import numpy as np

import matplotlib as mpl
from matplotlib import pyplot as plt
import matplotlib.patches as patches

from mpl_toolkits.axes_grid1 import make_axes_locatable
from matplotlib.colors import LogNorm

#--------------
# local imports
# -------------

#--------------
# local imports
# -------------

from azotea              import FITS_HEADER_TYPE, EXIF_HEADER_TYPE
from azotea.utils.image  import scan_non_empty_dirs
from azotea.utils.roi    import Rect, Point
from azotea.utils.sky    import get_debayered_for_channel

# ----------------
# Module constants
# ----------------

FITS_LOWER_EXTENSIONS = ('*.fit',  '*.fits', '*.fts')
EXIF_LOWER_EXTENSIONS = ('*.cr2', '*.nef', '*.orf', '*.pef')
FITS_EXTENSIONS       = FITS_LOWER_EXTENSIONS + tuple(s.upper() for s in FITS_LOWER_EXTENSIONS)
EXIF_EXTENSIONS       = EXIF_LOWER_EXTENSIONS + tuple(s.upper() for s in EXIF_LOWER_EXTENSIONS)

EXTENSIONS = EXIF_EXTENSIONS + FITS_EXTENSIONS


# -----------------------
# Module global variables
# -----------------------

log = logging.getLogger('azoplot')


# Algunos formatos de estilo de los plots
#mpl.rcParams['text.latex.unicode']=True
mpl.rcParams['text.usetex'] = False
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Verdana']
plt.rcParams['font.size'] = 8
plt.rcParams['lines.linewidth'] = 4.
plt.rcParams['axes.labelsize'] = 'small'
plt.rcParams['grid.linewidth'] = 1.0
plt.rcParams['grid.linestyle'] = ':'
plt.rcParams['xtick.minor.size'] = 4
plt.rcParams['xtick.major.size'] = 8
plt.rcParams['ytick.minor.size'] = 4 
plt.rcParams['ytick.major.size'] = 8
plt.rcParams['figure.figsize']   = 18,9
plt.rcParams['figure.subplot.bottom'] = 0.15
plt.rcParams['ytick.labelsize'] = 10
plt.rcParams['xtick.labelsize'] = 10
mpl.rcParams['xtick.direction'] = 'out'

# ------------------------
# Module utility functions
# ------------------------

def find_header_type(filepath):
    extension = '*' + os.path.splitext(filepath)[1]
    if extension in FITS_EXTENSIONS:
        result = FITS_HEADER_TYPE
    elif extension in EXIF_EXTENSIONS:
        result = EXIF_HEADER_TYPE
    else:
        result = None
        log.error("NO EXTENSION DETECTED")
    return result


def toDateTime(tstamp):
    for fmt in ('%Y:%m:%d %H:%M:%S','%Y-%m-%dT%H:%M:%S.%f', '%Y-%m-%dT%H:%M:%S'):
        try:
            tstamp_obj = datetime.datetime.strptime(tstamp, fmt)
        except ValueError as e:
            continue
        else:
            break
    if not tstamp_obj:
        raise IncorrectTimestampError(tstamp)
    else:
        return tstamp_obj.strftime('%Y-%m-%dT%H:%M:%S')


def metadata_fits(filepath):
    metadata = dict()
    with fits.open(filepath, memmap=False) as hdu_list:
        header = hdu_list[0].header
        metadata['header_type']  = FITS_HEADER_TYPE
        metadata['filepath'] = filepath
        metadata['height']   = header['NAXIS2']
        metadata['width']    = header['NAXIS1']
        metadata['model']    = header.get('INSTRUNE', 'Unknown')
        metadata['exptime']  = header.get('EXPTIME',  'Unknown')
        metadata['date_obs'] = header.get('DATE_OBS', 'Unknown')
        metadata['gain']     = header.get('LOG-GAIN', 'Unknown')
        metadata['iso']      = None
        focal_length = header.get('FOCALLEN')
        diameter     = header.get('APTDIA')
        metadata['focal_length'] = 'Unknown' if focal_length is None else focal_length
        metadata['f_number']     ='Unknown'  if focal_length is None and diameter is None else round(focal_length/diameter,1)
    return metadata


def metadata_exif(filepath):
    metadata = dict()
    with open(filepath, 'rb') as f:
        exif = exifread.process_file(f, details=False)
        if not exif:
            message = 'Could not open EXIF metadata'
            raise ValueError(message)
        metadata['header_type']  = EXIF_HEADER_TYPE
        metadata['filepath']     = filepath
        metadata['model']        = str(exif.get('Image Model', None)).strip()
        metadata['iso']          = str(exif.get('EXIF ISOSpeedRatings', None))
        metadata['focal_length'] = float(Fraction(str(exif.get('EXIF FocalLength', 0))))
        metadata['f_number']     = float(Fraction(str(exif.get('EXIF FNumber', 0))))
        metadata['exptime']      = float(Fraction(str(exif.get('EXIF ExposureTime', 0))))
        metadata['date_id'], row['time_id'], row['widget_date'], row['widget_time'] = toDateTime(str(exif.get('Image DateTime', None)))
        # Fixes missing Focal Length and F/ ratio
        metadata['focal_length'] = 'Unknown' if row['focal_length'] == 0 else metadata['focal_length']
        metadata['f_number']     = 'Unknown' if row['f_number']     == 0 else metadata['f_number']
        # Fixed GAIN for EXIF DSLRs that provide ISO sensivity
        metadata['gain'] = None
    # Get the real RAW dimensions instead
    with rawpy.imread(filepath) as img:
        imageHeight, imageWidth = img.raw_image.shape
    metadata['height']   = imageHeight
    metadata['width']    = imageWidth
    return metadata


def get_metadata(filepath, header_type):
    if header_type == FITS_HEADER_TYPE:
        metadata = metadata_fits(filepath)
    else:
        metadata = metadata_exif(filepath)
    return metadata


def centered_roi(metadata, width, height):
    rect = Rect(x1=0, y1=0, x2=width, y2=height)
    imageHeight, imageWidth = metadata['height'], metadata['width']
    imageHeight = imageHeight //2 # From raw dimensions without debayering
    imageWidth =  imageWidth  //2  # to dimensions we actually handle
    width, height = rect.dimensions()
    center=Point(imageWidth//2,imageHeight//2)
    x1 = (imageWidth  -  width)//2
    y1 = (imageHeight - height)//2
    rect += Point(x1,y1)  # Shift ROI using this (x1,y1) point
    result = rect.to_dict()
    return result


def get_pixels_and_plot(filepath, metadata, roi, bayer_pattern):
    if metadata['header_type'] == FITS_HEADER_TYPE:
        with fits.open(filepath, memmap=False) as hdu_list:
            raw_pixels = hdu_list[0].data
            # This must be executed unther the context manager
            # for raw_pixels to become valid
            plot_4_channels(raw_pixels, bayer_pattern, roi, metadata)
    else:
         with rawpy.imread(filepath) as img:
            raw_pixels = img.raw_image
            # This must be executed unther the context manager
            # for raw_pixels to become valid
            plot_4_channels(raw_pixels, bayer_pattern, roi, metadata)
           


def stat_display(axe, channel, roi):
    x1, x2, y1, y2 = roi['x1'], roi['x2'], roi['y1'], roi['y2']
    aver = channel[y1:y2,x1:x2].mean()
    std  = channel[y1:y2,x1:x2].std()
    aver_str = '\u03BC = ' + str(round(aver, 1))
    std_str  = '\u03C3 = ' + str(round(std,1))
    rect = patches.Rectangle((x1, y1), x2-x1, y2-y1, linewidth=1, edgecolor='k', facecolor='none')
    plt.text(x1+(x2-x1)/20, (y1+y2)/2-(y2-y1)/5, aver_str, ha='left', va='center')
    plt.text(x1+(x2-x1)/20, (y1+y2)/2+(y2-y1)/5, std_str, ha='left', va='center')
    axe.add_patch(rect)
    return aver, std



def set_title(figure, metadata):
    basename    = os.path.basename(metadata.get('filepath'))
    header_type = metadata.get('header_type')
    gain        = 'Unknown' if metadata.get('gain') is None else metadata.get('gain')
    iso         = 'Unknown' if metadata.get('iso') is None else metadata.get('iso')
    model       = 'Unknown' if metadata.get('model') is None else metadata.get('model') 
    exptime     = 'Unknown' if metadata.get('exptime') is None else metadata.get('exptime')
    date_obs    = 'Unknown' if metadata.get('date_obs') is None else metadata.get('date_obs')
    if header_type == FITS_HEADER_TYPE:
        label =f"{basename}\ncamera: {model}   gain = {gain}  exposure = {exptime} s."
    else:
        label =f"{basename}\ncamera: {model}   iso = {iso}  exposure = {exptime} s."
    figure.suptitle(label)


def add_subplot(figure, i, pixels, pixels_tag, roi, cmap, vmin, vmax):
    axe    = figure.add_subplot(220 + i)
    img    = axe.imshow(pixels,cmap=cmap,vmin=vmin,vmax=vmax)
    plt.text(0.05, 0.90,pixels_tag, ha='left', va='center', transform=axe.transAxes, fontsize=10)
    mean_center, std_center = stat_display(axe, pixels, roi)
    divider = make_axes_locatable(axe)
    caxe = divider.append_axes("right", size="5%", pad=0.05)
    figure.colorbar(img, cax=caxe)
    axe.axes.get_yaxis().set_ticks([])
    axe.axes.get_xaxis().set_ticks([])



def plot_4_channels(raw_pixels, bayer_pattern, roi, metadata, vmin=0, vmax=30000):
    figure = plt.figure(figsize=(10,6))
    set_title(figure, metadata)
    image_R1 = get_debayered_for_channel(raw_pixels, bayer_pattern, 'R')
    add_subplot(figure, 1, image_R1, 'R1', roi, 'Reds', vmin, vmax)
    image_G2 = get_debayered_for_channel(raw_pixels, bayer_pattern, 'G1')
    add_subplot(figure, 2, image_G2, 'G2', roi, 'Greens', vmin, vmax)
    image_G3 = get_debayered_for_channel(raw_pixels, bayer_pattern, 'G2')
    add_subplot(figure, 3, image_G3, 'G3', roi, 'Greens', vmin, vmax)
    image_B4 = get_debayered_for_channel(raw_pixels, bayer_pattern, 'B')
    add_subplot(figure, 4, image_B4, 'B4', roi, 'Blues', vmin, vmax)
    plt.tight_layout()
    plt.show()


# -----------------
# Auxiliary classes
# -----------------

class Cycler:
    def __init__(self, connection, filepath_list, **kwargs):
        self.filepath = filepath_list
        self.i = 0
        self.N = len(self.subject)
        self.reset()
        self.one_step(0)

    def next(self, event):
        self.i = (self.i +1) % self.N
        self.update(self.i)


    def prev(self, event):
        self.i = (self.i -1 + self.N) % self.N
        self.update(self.i)

        
    def reset(self):
        self.fig, self.axe = plt.subplots()
        # The dimensions are [left, bottom, width, height]
        # All quantities are in fractions of figure width and height.
        axnext = self.fig.add_axes([0.90, 0.01, 0.095, 0.050])
        self.bnext = Button(axnext, 'Next')
        self.bnext.on_clicked(self.next)
        axprev = self.fig.add_axes([0.79, 0.01, 0.095, 0.050])
        self.bprev = Button(axprev, 'Previous')
        self.bprev.on_clicked(self.prev)
        self.axe.set_xlabel("X, pixels")
        self.axe.set_ylabel("Y, pixels")
        self.axim = None
        self.sca = list()
        self.txt = list()
        self.prev_extent = dict()

    def update(self, i):
        # remove whats drawn in the scatter plots
        for sca in self.sca:
            sca.remove()
        self.sca = list()
        for txt in self.txt:
            txt.remove()
        self.txt = list()
        self.one_step(i)
        self.fig.canvas.draw_idle()
        self.fig.canvas.flush_events()

    def one_compute_step(self, i):
        fix = self.fix
        epsilon = self.epsilon
        subject_id = self.load(i)
        self.axe.set_title(f'Subject {subject_id}\nDetected light sources by DBSCAN (\u03B5 = {epsilon} px)')
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT source_x, source_y 
            FROM spectra_classification_v 
            WHERE subject_id = :subject_id
            ''',
            {'subject_id': subject_id}
        )
        coordinates = cursor.fetchall()
        N_Classifications = len(coordinates)
        coordinates = np.array(coordinates)
        model = cluster.DBSCAN(eps=epsilon, min_samples=2)
        # Fit the model and predict clusters
        yhat = model.fit_predict(coordinates)
        # retrieve unique clusters
        clusters = np.unique(yhat)
        log.info(f"Subject {subject_id}: {len(clusters)} clusters from {N_Classifications} classifications, ids: {clusters}")
        for cl in clusters:
            # get row indexes for samples with this cluster
            row_ix = np.where(yhat == cl)
            X = coordinates[row_ix, 0][0]; Y = coordinates[row_ix, 1][0]
            if(cl != -1):
                Xc = np.average(X); Yc = np.average(Y)
                sca = self.axe.scatter(X, Y,  marker='o', zorder=1)
                self.sca.append(sca)
                txt = self.axe.text(Xc+epsilon, Yc+epsilon, cl+1, fontsize=9, zorder=2)
                self.txt.append(txt)
            elif fix:
                start = max(clusters)+2 # we will shift also the normal ones ...
                for i in range(len(X)) :
                    cluster_id = start + i
                    sca = self.axe.scatter(X[i], Y[i],  marker='o', zorder=1)
                    self.sca.append(sca)
                    txt = self.axe.text(X[i]+epsilon, Y[i]+epsilon, cluster_id, fontsize=9, zorder=2)
                    self.txt.append(txt)
            else:
                sca = self.axe.scatter(X, Y,  marker='o', zorder=1)
                self.sca.append(sca)
                start = max(clusters)+2 # we will shift also the normal ones ...
                for i in range(len(X)) :
                    txt = self.axe.text(X[i]+epsilon, Y[i]+epsilon, cl, fontsize=9, zorder=2)
                    self.txt.append(txt)
      

# ===================
# Module entry points
# ===================

def do_single(filepath, options, i=1, N=1):
    log.info(f"prcessing {filepath}")
    header_type = find_header_type(filepath)
    metadata = get_metadata(filepath, header_type)
    roi = centered_roi(metadata, options.width, options.height)
    get_pixels_and_plot(filepath, metadata, roi, options.bayer_pattern)


def stats(options):
    if options.image_file:
        do_single(options.image_file, options)
    else:
        directories = scan_non_empty_dirs(options.images_dir, depth=0)
        directories = set(directories) # get reid of duplicates (a bug in scan_non_empty dir?)
        for directory in directories:
            paths_set = set()
            for extension in EXTENSIONS:
                alist  = glob.glob(os.path.join(directory, extension))
                paths_set  = paths_set.union(alist)
            N = len(paths_set)
            if N:
                log.warning(f"Scanning directory '{directory}'. Found {N} images matching '{EXTENSIONS}'")
            for i, filepath in enumerate(sorted(paths_set), start=1):
                try:
                    do_single(filepath, options, i, N)
                except (FileNotFoundError,) as e:
                    log.critical("[%s] Fatal error => %s", __name__, str(e) )
                    traceback.print_exc()
                    #continue
                except Exception as e:
                    raise e
