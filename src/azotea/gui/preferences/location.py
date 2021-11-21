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
import math
import random
import tkinter as tk
from   tkinter import ttk

# -------------------
# Third party imports
# -------------------

# ---------------
# Twisted imports
# ---------------

from twisted.logger import Logger

# -------------------
# Third party imports
# -------------------

from pubsub import pub

#--------------
# local imports
# -------------

from azotea.logger import setLogLevel
from azotea.utils import chop
from azotea.gui.widgets.contrib import ToolTip, LabelInput
from azotea.gui.widgets.combos import LocationCombo
from azotea.gui.preferences.base import PreferencesBaseFrame

# ----------------
# Module constants
# ----------------

# Support for internationalization
_ = gettext.gettext

NAMESPACE = 'GUI'

# -----------------------
# Module global variables
# -----------------------


def float_validator(new_val):
    try:
        float(new_val)
    except ValueError:
        return False
    else:
        return True


log  = Logger(namespace=NAMESPACE)


class LocationFrame(PreferencesBaseFrame):

    def __init__(self, *args, **kwargs):
        self._bookKeeping = {}
        super().__init__(*args, combo_class=LocationCombo, **kwargs)
       

    def build(self):
        super().build()
        container = self._container

        self._input['site_name'] = site_name = tk.StringVar()
        self._input['location'] = location = tk.StringVar()
        self._input['longitude'] = longitude = tk.DoubleVar()
        self._input['latitude'] = latitude = tk.DoubleVar()
        self._input['randomized'] = randomize = tk.BooleanVar()
        self._input['utc_offset'] = utc_offset = tk.DoubleVar()

        valid_coord = self.register(float_validator)
        input_args = {'validate': 'all','validatecommand': (valid_coord, '%P')}
        self._control['site_name'] = LabelInput(container, _("Place"), input_var=site_name, tip=_("Unique site name"))
        self._control['site_name'].pack(side=tk.TOP,fill=tk.X, expand=False, padx=10, pady=5)
        self._control['location'] = LabelInput(container, _("Location"), input_var=location, tip=_("City, town, etc."))
        self._control['location'].pack(side=tk.TOP,fill=tk.X, expand=False, padx=10, pady=5)
        self._control['utc_offset'] = LabelInput(container, _("Offset from UTC"), input_var=utc_offset, tip=_("i.e. +1 for GMT+1\nSet to 0 if camera time is in UTC!"))
        self._control['utc_offset'].pack(side=tk.TOP,fill=tk.X, expand=False, padx=10, pady=5)
        subframe = ttk.LabelFrame(container)
        subframe.pack(side=tk.TOP,fill=tk.X, expand=False, padx=0, pady=0)
        check_randomized = ttk.Checkbutton(self, text= _("Randomize"), variable=randomize)
        subframe.configure(labelwidget=check_randomized) 
        self._control['randomized'] = check_randomized 
        self._control['longitude'] = LabelInput(subframe, _("Longitude"), input_var=longitude, tip=_("In decimal degrees, negative West"))
        self._control['longitude'].pack(side=tk.TOP,fill=tk.X, expand=False, padx=10, pady=5)
        self._control['latitude'] = LabelInput(subframe, _("Latitude"), input_var=latitude, tip=_("RIn decimal degrees, negative South"))
        self._control['latitude'].pack(side=tk.TOP,fill=tk.X, expand=False, padx=10, pady=5)


    def isEmpty(self, data):
         return not bool(data) or (data['location'] == '') or (data['site_name'] == '')


    # # response to location_details_req
    # def detailsResp(self, data):
    #     '''Update with details from a single location'''
    #     super().detailsResp(data)
    #     if data:
    #         self._bookKeeping = {
    #             self._input['longitude'].get() : self._input['public_long'].get(),
    #             self._input['latitude'].get() :  self._input['public_lat'].get()
    #         }
         

    # # When pressing the save button
    # def onSaveButton(self):
    #     data = {key: widget.get() for key, widget in self._input.items()}
    #     if not self.isEmpty(data):
    #         for key in ('longitude','latitude','public_long','public_lat'):
    #             data[key] = float(self._input[key].get())
    #         self._control['save'].configure(state='disabled')
    #         pub.sendMessage(self._save_event, data=data)
    #         self._temp = data
