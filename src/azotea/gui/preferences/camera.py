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

import os
import gettext
import tkinter as tk
from   tkinter import ttk
import tkinter.filedialog

# -------------------
# Third party imports
# -------------------

from pubsub import pub
import PIL
from PIL import ImageTk

# ---------------
# Twisted imports
# ---------------

from twisted.logger import Logger

#--------------
# local imports
# -------------

from azotea import ICONS_DIR
from azotea.utils import chop
from azotea.utils.roi import Point
from azotea.gui.widgets.contrib import ToolTip, LabelInput
from azotea.gui.widgets.combos import CameraCombo
from azotea.gui.preferences.base import PreferencesBaseFrame
from azotea import FITS_HEADER_TYPE, EXIF_HEADER_TYPE

# ----------------
# Module constants
# ----------------

# Support for internationalization
_ = gettext.gettext

NAMESPACE = 'GUI'

# -----------------------
# Module global variables
# -----------------------


log  = Logger(namespace=NAMESPACE)



class CameraFrame(PreferencesBaseFrame):

    BAYER_PTN = ('RGGB', 'BGGR', 'GRBG', 'GBRG')
   
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, combo_class=CameraCombo, **kwargs)
        

    def build(self):
        super().build()
        container = self._container
        # Input widgets
        self._input['model'] = model = tk.StringVar()
        self._input['extension'] = extension = tk.StringVar()
        self._input['bias'] = bias = tk.IntVar()
        self._input['header_type'] = header_type = tk.StringVar()
        self._input['bayer_pattern'] = bayer_pattern = tk.StringVar()
        self._input['width'] = width = tk.IntVar()
        self._input['length'] = length = tk.IntVar()

        header_type.set(EXIF_HEADER_TYPE)

        button = ttk.Button(container, text=_("Choose image ..."), command=self.onImageChoose)
        button.pack(side=tk.TOP,fill=tk.X, expand=True, padx=5, pady=5)
        self._control['choose'] = button
        self._control['model'] = LabelInput(container, _("Model"), input_var=model, tip=_("Camera model from EXIF data"))
        self._control['model'].pack(side=tk.TOP,fill=tk.X, expand=True, padx=5, pady=5)

        subframe = ttk.Frame(container)
        subframe.pack(side=tk.TOP,fill=tk.BOTH, expand=True, padx=0, pady=0)
        self._control['extension'] = LabelInput(subframe, _("Extension"), input_var=extension, tip=_("File extension i.e: *.CR2"))
        self._control['extension'].grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        bias_args = {'from':0, 'to':16384, 'increment': 1}
        self._control['bias'] = LabelInput(subframe, _("Bias"), input_class=ttk.Spinbox, input_var=bias, input_args=bias_args, tip=_("Global pedestal level over 0"))
        self._control['bias'].grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        self._control['width'] = LabelInput(subframe, _("Columns"), input_class=ttk.Spinbox, input_var=width, tip=_("X resolution"))
        self._control['width'].grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self._control['length'] = LabelInput(subframe, _("Rows"), input_class=ttk.Spinbox, input_var=length, tip=_("Y resolution"))
        self._control['length'].grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
       
        subframe = ttk.LabelFrame(container, text=_('Header type'))
        subframe.pack(side=tk.TOP,fill=tk.X, expand=True, padx=5, pady=5)
        button1 = ttk.Radiobutton(subframe, text=EXIF_HEADER_TYPE, variable=header_type, value=EXIF_HEADER_TYPE)
        button1.grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        button2 = ttk.Radiobutton(subframe, text=FITS_HEADER_TYPE, variable=header_type, value=FITS_HEADER_TYPE)
        button2.grid(row=0, column=1, padx=10, pady=10, sticky=tk.E)
        subframe = ttk.LabelFrame(container, text=_('Color Filter Array'))
        subframe.pack(side=tk.TOP,fill=tk.X, expand=True, padx=10, pady=5)
        self._subframe = subframe
        self._control['bayer_pattern'] = ttk.Combobox(subframe, state='readonly', textvariable=bayer_pattern, values=self.BAYER_PTN)
        self._control['bayer_pattern'].grid(row=0, column=0, padx=5, pady=5)
        self._control['bayer_pattern'].bind('<<ComboboxSelected>>', self.onBayerSelected)

    
    def isEmpty(self, data):
         return not bool(data) or (data['model'] == '')

    def _loadIcon(self, pattern):
        path = os.path.join(ICONS_DIR, pattern + '.gif')
        img = PIL.ImageTk.PhotoImage(PIL.Image.open(path))
        icon = ttk.Label(self._subframe, image = img)
        icon.photo = img
        return icon

    def onBayerSelected(self, event):
        pattern = self._input['bayer_pattern'].get()
        icon = self._loadIcon(pattern)
        icon.grid(row=0, column=1, padx=10, pady=10)

    def onImageChoose(self):
        filename =  tk.filedialog.askopenfilename(
            initialdir = '.',
            title = 'Select image',
            filetypes = (('all files','*.*'),),
            parent = self.master,
        )
        if filename:
            pub.sendMessage('camera_choose_image_req', path=filename)

    # response to camera_details_req
    def detailsResp(self, data):
        super().detailsResp(data)
        if data:
            index = self.BAYER_PTN.index(data['bayer_pattern'])
            self._control['bayer_pattern'].current(index)
            icon = self._loadIcon(data['bayer_pattern'])
            icon.grid(row=0, column=1, padx=10, pady=10)
            self._input['header_type'].set(data['header_type'])

    def updateCameraInfoFromImage(self, info):
        if info:
            for key, value in info.items():
                 self._input[key].set(value)
   