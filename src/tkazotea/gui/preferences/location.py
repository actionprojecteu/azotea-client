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

from tkazotea.logger import setLogLevel
from tkazotea.utils import chop
from tkazotea.gui.widgets.contrib import ToolTip, LabelInput
from tkazotea.gui.widgets.combos import LocationCombo
from tkazotea.gui.preferences.base import PreferencesBaseFrame

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
        self._input['public_long'] = public_long = tk.DoubleVar()
        self._input['public_lat'] = public_lat = tk.DoubleVar()
        self._input['utc_offset'] = utc_offset = tk.DoubleVar()

        valid_coord = self.register(float_validator)
        input_args = {'validate': 'all','validatecommand': (valid_coord, '%P')}
        self._control['site_name'] = LabelInput(container, _("Place"), input_var=site_name, tip=_("Unique site name"))
        self._control['site_name'].pack(side=tk.TOP,fill=tk.X, expand=False, padx=10, pady=5)
        self._control['location'] = LabelInput(container, _("Location"), input_var=location, tip=_("City, town, etc."))
        self._control['location'].pack(side=tk.TOP,fill=tk.X, expand=False, padx=10, pady=5)
        self._control['utc_offset'] = LabelInput(container, _("Offset from UTC"), input_var=utc_offset, tip=_("i.e. +1 for GMT+1\nSet to 0 if camera time is in UTC!"))
        self._control['utc_offset'].pack(side=tk.TOP,fill=tk.X, expand=False, padx=10, pady=5)
        self._control['longitude'] = LabelInput(container, _("Longitude"), input_var=longitude, tip=_("In decimal degrees, negative West"))
        self._control['longitude'].pack(side=tk.TOP,fill=tk.X, expand=False, padx=10, pady=5)
        self._control['latitude'] = LabelInput(container, _("Latitude"), input_var=latitude, tip=_("In decimal degrees, negative South"))
        self._control['latitude'].pack(side=tk.TOP,fill=tk.X, expand=False, padx=10, pady=5)
        subframe = ttk.LabelFrame(container, text=_("Non editable"))
        subframe.pack(side=tk.TOP,fill=tk.X, expand=False, padx=0, pady=0)
        self._control['public_long'] = LabelInput(subframe, _("Public Longitude"), input_var=public_long, tip=_("Randomized longitude"))
        self._control['public_long'].pack(side=tk.TOP,fill=tk.X, expand=False, padx=10, pady=5)
        self._control['public_lat'] = LabelInput(subframe, _("Public Latitude"), input_var=public_lat, tip=_("Randomized latitude"))
        self._control['public_lat'].pack(side=tk.TOP,fill=tk.X, expand=False, padx=10, pady=5)
        

    def _randomize(self):
        longitude = self._input['longitude'].get()
        latitude = self._input['latitude'].get()
        if not longitude in self._bookKeeping:
            log.info('Randomizing public coordinates')
            # Includes +- 1Km uncertainty in coordinates
            delta_long  = random.uniform(-1,1)*(1/6371)*math.cos(math.radians(latitude))
            delta_lat   = random.uniform(-1,1)*(1/6371)
            random_long = longitude + math.degrees(delta_long)
            random_lat  = latitude  + math.degrees(delta_lat)
            self._input['public_long'].set(random_long)
            self._input['public_lat'].set(random_lat)
            self._bookKeeping[longitude] = random_long
            self._bookKeeping[latitude]  = random_lat


    def isEmpty(self, data):
         return not bool(data) or (data['location'] == '') or (data['site_name'] == '')
     
    def _enableWidgets(self, flag):
        super()._enableWidgets(flag)
        self._control['public_long'].configure(state="disabled")
        self._control['public_lat'].configure(state="disabled")

    def _enableROEntry(self):
        self._control['public_long'].configure(state="normal")
        self._control['public_lat'].configure(state="normal")

    def _disableROEntry(self):
        self._control['public_long'].configure(state="disabled")
        self._control['public_lat'].configure(state="disabled")


    # response to location_details_req
    def detailsResp(self, data):
        '''Update with details from a single location'''
        super().detailsResp(data)
        if data:
            self._bookKeeping = {
                self._input['longitude'].get() : self._input['public_long'].get(),
                self._input['latitude'].get() :  self._input['public_lat'].get()
            }
         

    # When pressing the save button
    def onSaveButton(self):
        self._randomize()
        data = {key: widget.get() for key, widget in self._input.items()}
        if not self.isEmpty(data):
            for key in ('longitude','latitude','public_long','public_lat'):
                data[key] = float(self._input[key].get())
            self._control['save'].configure(state='disabled')
            pub.sendMessage(self._save_event, data=data)
            self._temp = data
