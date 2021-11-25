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

from azotea.gui import IMG_ROI
from azotea.utils import chop 
from azotea.utils.roi import Point, Rect
from azotea.gui.widgets.contrib import ToolTip, LabelInput
from azotea.gui.widgets.combos  import ROICombo
from azotea.gui.preferences.base import PreferencesBaseFrame

# ----------------
# Module constants
# ----------------

# Support for internationalization
_ = gettext.gettext

NAMESPACE = 'gui'

MANUAL_METHOD  = 'Manual selection'
AUTO_METHOD    = 'Automatic centering'
DEFAULT_WIDTH  = 500
DEFAULT_HEIGHT = 400

# -----------------------
# Module global variables
# -----------------------


log  = Logger(namespace=NAMESPACE)


class ROIFrame(PreferencesBaseFrame):

    def __init__(self, *args, **kwargs):
        self._labels = dict()
        super().__init__(*args, combo_class=ROICombo, **kwargs)
        

    def build(self):
        super().build()
        container = self._container

        # Input
        self._input['display_name'] = display_name = tk.StringVar()
        self._input['comment'] = comment = tk.StringVar()

        method_var = tk.StringVar()
        method_var.set(AUTO_METHOD) # This is not part of the input valus to be passed
        self._method = method_var

        subframe = ttk.LabelFrame(container, text=_('Selection method'))
        subframe.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
       

        # Selection method
        subsubframe = ttk.Frame(subframe)
        subsubframe.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        button = ttk.Radiobutton(subsubframe, text=_("Manual selection"), variable=method_var,value=MANUAL_METHOD, command=self.onMethodSelected)
        button.pack(side=tk.TOP, anchor=tk.W,  padx=5, pady=5)
        self._control['radio_auto'] = button
        button = ttk.Radiobutton(subsubframe, text=_("Automatic centering"), variable=method_var, value=AUTO_METHOD, command=self.onMethodSelected)
        button.pack(side=tk.TOP, anchor=tk.W,  padx=5, pady=5)
        self._control['radio_manual'] = button

        # Automatic selection
        # AQUI ME QUEDE. HAY QUE REPASAR
        subframe = ttk.LabelFrame(container, text=_("Automatic centering"))
        subframe.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
        subframeL = ttk.Frame(subframe)
        subframeL.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=0, pady=0)
        subframeR = ttk.Frame(subframe)
        subframeR.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=0, pady=0)
        label = ttk.Label(subframeL, text="Width")
        label.grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self._widthVar = widthVar = tk.IntVar()
        widthVar.set(DEFAULT_WIDTH)
        spin = ttk.Spinbox(subframeL, textvariable=widthVar, width=5, to=9999)
        spin.grid(row=1, column=0, sticky=tk.W ,padx=5, pady=5)
        self._control['width'] = spin
        label = ttk.Label(subframeL, text="Height")
        label.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        self._heightVar = heightVar = tk.IntVar()
        heightVar.set(DEFAULT_HEIGHT)
        spin = ttk.Spinbox(subframeL, textvariable=heightVar, width=5, to=9999)
        spin.grid(row=1, column=1, sticky=tk.W ,padx=5, pady=5)
        self._control['height'] = spin
        button = ttk.Button(subframeR, text=_("Choose Image"), command=self.onFileButton)
        button.pack(side=tk.RIGHT,fill=tk.BOTH,  padx=5, pady=2)
        self._control['imgbutton'] = button
        
        # Manual Region of Interest
        subframe = ttk.LabelFrame(container, text=_("Manual selection"))
        subframe.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
        subframeL = ttk.Frame(subframe)
        subframeL.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=0, pady=0)
        subframeR = ttk.Frame(subframe)
        subframeR.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=0, pady=0)
        roi_args = {'from':0, 'to':9999, 'increment': 1}
        for key,tag,row,col in (('x1','x1',0,0),('y1','y1',0,1),('x2','x2',1,0),('y2','y2',1,1)):
            valueVar = tk.IntVar()
            self._input[key]=valueVar
            label = ttk.Label(subframeL, text=tag)
            label.grid(row=row*2, column=col, sticky=tk.W, padx=5, pady=5)
            spin = ttk.Spinbox(subframeL, textvariable=valueVar, width=5, from_= 0, to=9999)
            spin.grid(row=2*row+1, column=col, sticky=tk.W ,padx=5, pady=5)
            self._control[key] = spin
        #
        icon = self._loadIcon(subframeR)
        icon.pack(side=tk.RIGHT,fill=tk.BOTH,  padx=5, pady=2)
        # automatic Comment
        self._control['comment'] = LabelInput(container, _("Comment"), input_var=comment)
        self._control['comment'].pack(side=tk.TOP, fill=tk.X, expand=True, padx=5, pady=5)

    def _loadIcon(self, frame):
        img = PIL.ImageTk.PhotoImage(PIL.Image.open(IMG_ROI))
        icon = ttk.Label(frame, image = img)
        icon.photo = img
        return icon

    def isEmpty(self, data):
         return all([val == 0 for key, val in data.items()])
         

    def _blankForm(self):
        super()._blankForm()
        self._method.set(AUTO_METHOD)
            

    def detailsResp(self, data):
        '''Update with details from a single ROI'''
        if data:
            self._combo.set(data)
            for key,value in data.items():
                self._input[key].set(value)
            rect = Rect.from_dict(data)
            w, h = rect.dimensions()
            self._widthVar.set(w)
            self._heightVar.set(h)


    def onEditCheckBox(self):
        super().onEditCheckBox()
        self.onMethodSelected()
        
        
    def onMethodSelected(self):
        value = self._method.get()
        if value == MANUAL_METHOD:
            self._control['imgbutton'].configure(state='disabled')
            for key in ('x1','y1','x2','y2'):
                self._control[key].configure(state='normal')
            for key in ('width','height'):
                self._control[key].configure(state='disabled')
        else:
            self._control['imgbutton'].configure(state='enabled')
            for key in ('x1','y1','x2','y2'):
                self._control[key].configure(state='disabled')
            for key in ('width','height'):
                self._control[key].configure(state='normal')



    # When pressing the Choose Image button
    def onFileButton(self):
        filename =  tk.filedialog.askopenfilename(
            initialdir = '.',
            title = 'Select file',
            filetypes = (('all files','*.*'),),
            parent = self.master
        )
        if filename:
            data = {key: widget.get() for key,widget in  self._input.items()}
            rect = Rect.from_dict(data)
            rect = Rect(x1 = 0, y1 = 0, x2 = self._widthVar.get(), y2 = self._heightVar.get())
            pub.sendMessage('roi_set_automatic_req', filename=filename, rect=rect)


    def automaticROIResp(self, data):
        for key, widget in self._input.items():
            widget.set(data[key])
        

    def saveOkResp(self):
        super().saveOkResp()
        # The rect reorders cooordinates so that x1 < x2 & y1 < y2
        rect = Rect.from_dict({ key: self._input[key].get() for key in ('x1', 'y1', 'x2', 'y2')})        
        self._input['x1'].set(rect.x1), 
        self._input['x2'].set(rect.x2), 
        self._input['y1'].set(rect.y1), 
        self._input['y2'].set(rect.y2)
        w, h = rect.dimensions()
        self._widthVar.set(w)
        self._heightVar.set(h)



    