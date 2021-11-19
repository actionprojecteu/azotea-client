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

from azotea.gui import ICONS_DIR
from azotea.utils import chop
from azotea.utils.roi import Point
from azotea.gui.widgets.contrib import ToolTip, LabelInput

# ----------------
# Module constants
# ----------------


TIME_OPTIONS_ALL     = 'All'
TIME_OPTIONS_SESSION = 'Session'
TIME_OPTIONS_NIGHT   = 'Last night'

# Support for internationalization
_ = gettext.gettext

NAMESPACE = 'GUI'

# -----------------------
# Module global variables
# -----------------------


log  = Logger(namespace=NAMESPACE)



class MiscelaneaFrame(ttk.Frame):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._input = {}
        self._control = {}
        self.build()
        self._blankForm()
       
    def start(self):
         pub.sendMessage('misc_details_req')

    def build(self):
        top_frame = ttk.Frame(self)
        top_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=0)
        bottom_frame = ttk.Frame(self)
        bottom_frame.pack(side=tk.TOP, fill=tk.X, expand=True, padx=5, pady=0)

        # Optics section
        subframe = ttk.LabelFrame(top_frame,text=_("Optics"))
        subframe.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self._input['focal_length']  = v1 = tk.DoubleVar()
        self._input['f_number']      = v2 = tk.DoubleVar()

        widget = LabelInput(subframe, _("Focal Length (mm)"), input_var=v1)
        widget.pack(side=tk.TOP, fill=tk.X, expand=True, padx=5, pady=0)
        self._control['focal_length'] = widget
        widget = LabelInput(subframe, _("f/ number"), input_var=v2)
        widget.pack(side=tk.TOP, fill=tk.X, expand=True, padx=5, pady=0)
        self._control['f_number'] = widget
        
        # Lower Buttons
        button = ttk.Button(bottom_frame, text=_("Save"), command=self.onSaveButton)
        button.pack(side=tk.LEFT,fill=tk.X, expand=True, padx=5, pady=5)
        self._control['save'] = button
        button = ttk.Button(bottom_frame, text=_("Delete"), command=self.onDeleteButton)
        button.pack(side=tk.LEFT,fill=tk.X, expand=True, padx=5, pady=5)
        self._control['del'] = button

   
    def _blankForm(self):
        for key, widget in self._input.items():
            widget.set(0)

    def isEmpty(self, data):
         return not bool(data) or (data['focal_length'] == 0) or (data['f_number'] == 0)

    # response to misc_details_req
    def detailsResp(self, data):
        if data:
            for key,value in data.items():
                if value is not None:
                    self._input[key].set(value)
            
    # When pressing the Save button
    def onSaveButton(self):
        '''When pressing the Save Button'''
        data = { key: widget.get() for key, widget in self._input.items()}
        if not self.isEmpty(data):
            self._control['save'].configure(state='disabled')
            pub.sendMessage('misc_save_req', data=data)

    # response to preferences.cameras.save
    def saveOkResp(self):
        self._control['save'].configure(state='enabled')


    # When pressing the Delete button
    def onDeleteButton(self):
        data = { key: widget.get() for key,widget in self._input.items()}
        if not self.isEmpty(data):
            self._control['del'].configure(state='disabled')
            pub.sendMessage('misc_delete_req', data=data)

    # response to misc_delete_req
    def deleteOkResponse(self, count):
        self._control['del'].configure(state='enabled')
        self._blankForm()

    # response to misc_delete_req
    def deleteErrorResponse(self, count):
        message = _("I dont't know what to say.")
        tk.messagebox.showwarning(message=message, title=_("Preferences"), parent=self.master)
        self._control['del'].configure(state='enabled')

