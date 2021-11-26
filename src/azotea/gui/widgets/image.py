# ----------------------------------------------------------------------
# Copyright (c) 2020
#
# See the LICENSE file for details
# see the AUTHORS file for authors
# ----------------------------------------------------------------------

#################################
## APPLICATION SPECIFIC WIDGETS #
#################################

#--------------------
# System wide imports
# -------------------

import math
import gettext
import tkinter as tk
from   tkinter import ttk
import tkinter.filedialog

# -------------------
# Third party imports
# -------------------

import rawpy
import PIL
from PIL import ImageTk


# ---------------
# Twisted imports
# ---------------

from twisted.logger import Logger

# -------------
# local imports
# -------------

from azotea.gui.widgets.contrib import ToolTip

# ----------------
# Module constants
# ----------------

# Support for internationalization
_ = gettext.gettext

NAMESPACE = 'gui'

# -----------------------
# Module global variables
# -----------------------

log  = Logger(namespace=NAMESPACE)

# -----------------
# helper functions
# -----------------


# -----------------
# Application Class
# -----------------

class ImageDialog(tk.Toplevel):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.build()
        
    def build(self, ncols=3):
        self.title(_("Image Viewer"))

        # TOP superframe
        frame = ttk.Frame(self,  borderwidth=2, relief=tk.GROOVE)
        frame.pack(side=tk.TOP, expand=True, fill=tk.X, padx=5, pady=5)

        self.canvas = tk.Canvas(frame, width=300, height=200)
        self.canvas.pack(side=tk.TOP, expand=True, fill=tk.X, padx=5, pady=5)

     