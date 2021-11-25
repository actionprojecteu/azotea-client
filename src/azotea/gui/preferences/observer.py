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

from azotea.utils import chop
from azotea.gui.widgets.contrib import ToolTip, LabelInput
from azotea.gui.widgets.combos  import ObserverCombo
from azotea.gui.preferences.base import PreferencesBaseFrame

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


class ObserverFrame(PreferencesBaseFrame):

    def __init__(self, *args,  **kwargs):
        super().__init__(*args, combo_class=ObserverCombo, **kwargs)

    def build(self):
        super().build()
        container = self._container

        # Input Widgets
        self._input['family_name'] = family_name = tk.StringVar()
        self._input['surname'] = surname = tk.StringVar()
        self._input['affiliation'] =affiliation = tk.StringVar()
        self._input['acronym'] = acronym = tk.StringVar()
        
        subframe = ttk.LabelFrame(container,text=_("Personal data"))
        subframe.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)
        self._control['family_name'] = LabelInput(subframe, _("Family Name"), input_var=family_name)
        self._control['family_name'].pack(side=tk.TOP, fill=tk.X, expand=True, padx=10, pady=5)
        self._control['surname'] = LabelInput(subframe, _("Surname"), input_var=surname)
        self._control['surname'].pack(side=tk.TOP, fill=tk.X, expand=True, padx=10, pady=5)
        
        subframe = ttk.LabelFrame(container,text=_("Affiliation"))
        subframe.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)
        self._control['affiliation'] = LabelInput(subframe, _("Name"), input_var=affiliation)
        self._control['affiliation'].pack(side=tk.TOP, fill=tk.X, expand=True, padx=10, pady=5)
        self._control['acronym'] = LabelInput(subframe, _("Acronym"), input_var=acronym)
        self._control['acronym'].pack(side=tk.TOP, fill=tk.X, expand=True, padx=10, pady=5)
        

    def isEmpty(self, data):
         return not bool(data) or (data['family_name'] == '') or (data['surname'] == '')

 