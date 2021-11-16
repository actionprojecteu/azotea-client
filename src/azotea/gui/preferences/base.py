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

# ---------------
# Twisted imports
# ---------------

from twisted.logger import Logger

#--------------
# local imports
# -------------

from azotea.utils import chop
from azotea.gui.widgets.contrib import ToolTip, LabelInput
from azotea.gui.widgets.combos import DimensionCombo

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


class PreferencesBaseFrame(ttk.Frame):

    def __init__(self, parent, label, initial_event, save_event, delete_event, detail_event, default_event, purge_event=None, combo_class=DimensionCombo, **kwargs):
        super().__init__(parent, **kwargs)
        self._input = {}
        self._control = {}
        self._label = label
        self._initial_event = initial_event
        self._save_event = save_event
        self._delete_event = delete_event
        self._purge_event = purge_event
        self._detail_event = detail_event
        self._default_event = default_event
        self._enableVar = tk.BooleanVar()
        self.comboClass = combo_class
        self._enableVar.set(False)
        self.build()
        
    def start(self):
        self.onEditCheckBox() # Trigger first state change
        pub.sendMessage(self._initial_event)

    def build(self):
        # Upper Combo Box
        # top_frame = ttk.LabelFrame(self, text=self._label)
        # top_frame.pack(side=tk.TOP,  expand=True, fill=tk.BOTH, padx=10, pady=5)
        # combo = ttk.Combobox(top_frame, state='readonly', values=[])
        # combo.pack(side=tk.TOP, fill=tk.X, expand=True,  padx=10, pady=5)
        # combo.bind('<<ComboboxSelected>>', self.onComboSelection)
        # self._combo = combo

        combo = self.comboClass(self, text=self._label, command=self.onComboSelection)
        combo.pack(side=tk.TOP, fill=tk.X, expand=True,  padx=10, pady=5)
        self._combo = combo

        # Middle frame holding a checkbutton and the contailer frame for children
        middle_frame = ttk.LabelFrame(self, text="Fix me")
        middle_frame.pack(side=tk.TOP, expand=True, fill=tk.BOTH, padx=10, pady=5)
        check_adv = ttk.Checkbutton(self, text= _("Edit"), variable=self._enableVar, command=self.onEditCheckBox)
        middle_frame.configure(labelwidget=check_adv)  # 

        # Where to really put the children  widgets
        container_frame = ttk.Frame(middle_frame)
        container_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True,  padx=10, pady=5)
        self._container = container_frame

        bottom_frame = ttk.Frame(middle_frame)
        bottom_frame.pack(side=tk.BOTTOM, expand=True, fill=tk.X, padx=10, pady=5)

        # Lower Buttons
        button = ttk.Button(bottom_frame, text=_("Save"), command=self.onSaveButton)
        button.pack(side=tk.LEFT,fill=tk.BOTH, expand=True, padx=10, pady=5)
        self._control['save'] = button
        if self._purge_event:
            button = ttk.Button(bottom_frame, text=_("Purge"), command=self.onPurgeButton)
            button.pack(side=tk.LEFT,fill=tk.BOTH, expand=True, padx=10, pady=5)
            self._control['purge'] = button
        button = ttk.Button(bottom_frame, text=_("Delete"), command=self.onDeleteButton)
        button.pack(side=tk.RIGHT,fill=tk.BOTH, expand=True, padx=10, pady=5)
        self._control['delete'] = button


    def isEmpty(self, data):
        '''When data contains nouseful value for save/delete/purge'''
        raise NotImplementedError

    def _blankForm(self):
        self._combo.clear()
        for key, widget in self._input.items():
            if type(widget) in (tk.IntVar, tk.BooleanVar, tk.DoubleVar):
                widget.set(0)
            else:
                widget.set('')

    # response to initial_event
    def listResp(self, data):
        '''Update Combobox with all input data'''
        if data:
            self._combo.fill(data)
        else:
            self._blankForm()


    def detailsResp(self, data):
        '''Update with details from a single observer'''
        if data:
            self._combo.set(data)
            for key, value in data.items():
                self._input[key].set(value)

        

    # When selecting something with combobox
    def onComboSelection(self, event):
        data = self._combo.get()      
        pub.sendMessage(self._default_event, data=data)
        self._enableVar.set(False)
        self._enableWidgets(False)

    # ----------------------
    # Enable/Disable edition
    # ----------------------

    def _enableWidgets(self, flag):
        if flag:  
            for key, widget in self._control.items():
                if type(widget) in (ttk.Checkbutton, ttk.Checkbutton, ttk.Button, ttk.Button):
                    widget.configure(state='enabled')
                elif type(widget) in (ttk.Radiobutton, ttk.Radiobutton,):
                    widget.configure(state='normal')
                elif type(widget) in (ttk.Combobox,):
                    widget.configure(state='readonly')
                else:
                    widget.configure(state='normal')
        else:
            for key, widget in self._control.items():
                widget.configure(state='disabled')

    def onEditCheckBox(self):
        flag = self._enableVar.get()
        self._enableWidgets(flag)
        if flag:
            data = self._combo.get()
            if not self.isEmpty(data):
                pub.sendMessage(self._detail_event, data=data)



    # ------------
    # Save Control
    # ------------

    # When pressing the save button
    def onSaveButton(self):
        data = {key: widget.get() for key, widget in self._input.items()}
        if not self.isEmpty(data):
            self._control['save'].configure(state='disabled')
            pub.sendMessage(self._save_event, data=data)
            self._temp = data

    # response from controller to save button
    def saveOkResp(self):
        data = {key: widget.get() for key, widget in self._input.items()}
        self._combo.set(data)
        self._control['save'].configure(state='enabled')
        pub.sendMessage(self._default_event, data=self._temp)
        self._temp = None

    # --------------
    # Delete Control
    # --------------

    # When pressing the delete button
    def onDeleteButton(self):
        data = {key: widget.get() for key, widget in self._input.items()}
        if not self.isEmpty(data):
            self._control['delete'].configure(state='disabled')
            pub.sendMessage(self._delete_event, data=data)

    # Ok response to delete request
    def deleteOkResponse(self, count):
        self._control['delete'].configure(state='enabled')

    # Error response to delete request
    def deleteErrorResponse(self, count):
        message = _("Item referenced in database!\nCannot delete.")
        tk.messagebox.showwarning(message=message, title='Preferences',parent=self.master)
        self._control['delete'].configure(state='enabled')

    # -------------
    # Purge Control
    # -------------

    # When pressing the purge button
    def onPurgeButton(self):
        data = {key: widget.get() for key, widget in self._input.items()}
        if not self.isEmpty(data):
            self._control['purge'].configure(state='disabled')
            pub.sendMessage(self._purge_event, data=data)

    # response to observer_purge_req
    def purgeOkResponse(self, count):
        if count:
            message = _("Purged {0} previous versions.").format(count)
            tk.messagebox.showinfo(message=message, title=_("Preferences"), parent=self.master)
        self._control['purge'].configure(state='enabled')

    # response to observer_purge_req
    def purgeErrorResponse(self, count):
        message = _("{0} previous versions referenced in database!\nCannot delete.").format(count)
        tk.messagebox.showwarning(message=message, title=_("Preferences"), parent=self.master)
        self._control['purge'].configure(state='enabled')

