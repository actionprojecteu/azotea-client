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

# -------------------
# Third party imports
# -------------------

import numpy as np

import matplotlib as mpl
from matplotlib import pyplot as plt

from mpl_toolkits.axes_grid1 import make_axes_locatable
from matplotlib.colors import LogNorm

#--------------
# local imports
# -------------
from azotea.utils.sky import get_debayered_for_channel

# ----------------
# Module constants
# ----------------

# -----------------------
# Module global variables
# -----------------------


# Algunos formatos de estilo de los plots
mpl.rcParams['text.latex.unicode']=True
mpl.rcParams['text.usetex']=False
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Verdana']
plt.rcParams['font.size'] = 8
plt.rcParams['lines.linewidth'] = 4.
plt.rcParams['axes.labelsize'] = 'small'
plt.rcParams['grid.linewidth'] = 1.0
plt.rcParams['grid.linestyle'] = ':'
plt.rcParams['xtick.minor.size']=4
plt.rcParams['xtick.major.size']=8
plt.rcParams['ytick.minor.size']=4
plt.rcParams['ytick.major.size']=8
plt.rcParams['figure.figsize'] = 18,9
plt.rcParams['figure.subplot.bottom'] = 0.15
plt.rcParams['ytick.labelsize'] = 10
plt.rcParams['xtick.labelsize'] = 10
mpl.rcParams['xtick.direction'] = 'out'

# -------------------
# Auxiliary functions
# -------------------

def stat_display(channel, roi):
    x1, x2, y1, y2 = roi['x1'], roi['x2'], roi['y1'], roi['y2']

    plt.plot((x1,x1),(y1,y2),'k-',lw=1)
    plt.plot((x2,x2),(y1,y2),'k-',lw=1)
    plt.plot((x1,x2),(y1,y1),'k-',lw=1)
    plt.plot((x1,x2),(y2,y2),'k-',lw=1)
   
    aver = channel[y1:y2,x1:x2].mean()
    std  = channel[y1:y2,x1:x2].std()
    
    plt.text(x1+(x2-x1)/20, (y1+y2)/2-(y2-y1)/5, str(round(aver, 1)),   ha='left', va='center')
    plt.text(x1+(x2-x1)/20, (y1+y2)/2+(y2-y1)/5, str(round(std,1)), ha='left', va='center')
    return aver, std



# -------------------
# Important functions
# -------------------

def myplot(raw_pixels, bayer_pattern, roi, metadata=None, vmin=0, vmax=30000):

    metadata = dict() if metadata is None else metadata

    image_R1 = get_debayered_for_channel(raw_pixels, bayer_pattern, 'R')
    image_G2 = get_debayered_for_channel(raw_pixels, bayer_pattern, 'G1')
    image_G3 = get_debayered_for_channel(raw_pixels, bayer_pattern, 'G2')
    image_B4 = get_debayered_for_channel(raw_pixels, bayer_pattern, 'B')

    figura = plt.figure(figsize=(10,6))

    ax1    = figura.add_subplot(221)
    img    = ax1.imshow(image_R1,cmap='Reds',vmin=vmin,vmax=vmax)
    plt.text(0.05, 0.90,'R1', ha='left', va='center', transform=ax1.transAxes,fontsize=10)
    r1_mean_center,r1_std_center = stat_display(image_R1, roi)
    divider = make_axes_locatable(ax1)
    cax1 = divider.append_axes("right", size="5%", pad=0.05)
    figura.colorbar(img, cax=cax1)

    ax3=figura.add_subplot(222)
    img = ax3.imshow(image_G2,cmap='Greens',vmin=vmin,vmax=vmax)
    plt.text(0.05, 0.90,'G2', ha='left', va='center', transform=ax3.transAxes,fontsize=10)
    g2_mean_center,g2_std_center = stat_display(image_G2, roi)
    divider = make_axes_locatable(ax3)
    cax3 = divider.append_axes("right", size="5%", pad=0.05)
    figura.colorbar(img, cax=cax3)
    ax3.axes.get_yaxis().set_ticks([])
    ax3.axes.get_xaxis().set_ticks([])

    ax5=figura.add_subplot(223)
    img = ax5.imshow(image_G3,cmap='Greens',vmin=vmin,vmax=vmax)
    plt.text(0.05, 0.90,'G3', ha='left', va='center', transform=ax5.transAxes,fontsize=10)
    g3_mean_center,g3_std_center = stat_display(image_G3, roi)
    divider = make_axes_locatable(ax5)
    cax5 = divider.append_axes("right", size="5%", pad=0.05)
    figura.colorbar(img, cax=cax5)
    ax5.axes.get_yaxis().set_ticks([])
    ax5.axes.get_xaxis().set_ticks([])

    ax7=figura.add_subplot(224)
    img = ax7.imshow(image_B4,cmap='Blues',vmin=vmin,vmax=vmax)
    plt.text(0.05, 0.90,'B4', ha='left', va='center', transform=ax7.transAxes,fontsize=10)
    b4_mean_center,b4_std_center = stat_display(image_B4, roi)
    divider = make_axes_locatable(ax7)
    cax7 = divider.append_axes("right", size="5%", pad=0.05)
    figura.colorbar(img, cax=cax7)
    ax7.axes.get_yaxis().set_ticks([])
    ax7.axes.get_xaxis().set_ticks([])

 
    basename    = os.path.basename(metadata.get('filepath'))
    header_type = metadata.get('header_type')
    gain        = metadata.get('gain')
    iso         = metadata.get('iso')
    model       = metadata.get('model')
    exptime     = metadata.get('exptime')
    date_obs    = metadata.get('date_obs')

    if header_type == 'FITS_HEADER_TYPE':
        label =f"{model}   gain = {gain}  exposure = {exptime} s."
    else:
        label =f"{model}   iso = {iso}  exposure = {exptime} s."

    plt.text(-0.0, 1.05, basename, ha='left', va='center', transform=ax7.transAxes, fontsize=10)
    plt.text(0.4, 1.12,  date_obs, ha='left', va='center', transform=ax7.transAxes,fontsize=10)    
    plt.text(0.4, 1.05,  str(model)+'  gain='+str(gain)+'  '+str(exposure)+' s', ha='left', va='center', transform=ax7.transAxes,fontsize=10)
   
    plt.tight_layout()
    plt.show()

