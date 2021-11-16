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
import urllib.parse
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


class URLSchemeError(ValueError):
    pass 

class URLHostameError(ValueError):
    pass 

class URLPathError(ValueError):
    pass 


class PublishingFrame(ttk.Frame):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._input = {}
        self._control = {}
        self.build()
        self._blankForm()
       
    def start(self):
         pub.sendMessage('publishing_details_req')
         log.info("CUCUUUUUU")

    def build(self):
        top_frame = ttk.Frame(self)
        top_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=0)
        bottom_frame = ttk.Frame(self)
        bottom_frame.pack(side=tk.TOP, fill=tk.X, expand=True, padx=5, pady=0)

        # URL section
        self._input['url']  = v0 = tk.StringVar()
        widget = LabelInput(top_frame, _("URL"), input_var=v0)
        widget.pack(side=tk.TOP, fill=tk.X, expand=True, padx=5, pady=5)
        self._control['url'] = widget
        ToolTip(widget, text=_("Contact UCM for details"))

        # Credentials section
        subframe = ttk.LabelFrame(top_frame,text=_("Credentials"))
        subframe.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self._input['username']  = v1 = tk.StringVar()
        self._input['password']  = v2 = tk.StringVar()
        self._confirm  = v3 = tk.StringVar()

        opts = {'show': '*'}
        widget = LabelInput(subframe, _("Username"), input_var=v1)
        widget.pack(side=tk.TOP, fill=tk.X, expand=True, padx=5, pady=0)
        self._control['username'] = widget
        ToolTip(widget, text=_("Contact UCM for details"))

        widget = LabelInput(subframe, _("Password"), input_var=v2, input_args=opts)
        widget.pack(side=tk.TOP, fill=tk.X, expand=True, padx=5, pady=0)
        self._control['password'] = widget
        ToolTip(widget, text=_("Contact UCM for details"))

        widget = LabelInput(subframe, _("Confirm Password"), input_var=v3, input_args=opts)
        widget.pack(side=tk.TOP, fill=tk.X, expand=True, padx=5, pady=0)
        self._control['confirm'] = widget
        
        # Lower Buttons
        button = ttk.Button(bottom_frame, text=_("Save"), command=self.onSaveButton)
        button.pack(side=tk.LEFT,fill=tk.X, expand=True, padx=5, pady=5)
        self._control['save'] = button
        button = ttk.Button(bottom_frame, text=_("Clear"), command=self.onClearButton)
        button.pack(side=tk.LEFT,fill=tk.X, expand=True, padx=5, pady=5)
        self._control['clear'] = button

   
    def _checkPassword(self):
        return True if self._input['password'].get() == self._confirm.get() else False

    def _checkURL(self):
        url = self._input['url'].get()
        parts = urllib.parse.urlparse(url, allow_fragments=False)
        if parts.scheme != 'http' and parts.scheme != 'https':
            raise URLSchemeError( _("Bad URL scheme: {0}".format(parts.scheme)))
        if not parts.hostname:
            raise URLHostnameError( _("Bad URL hostname: {0}".format(parts.hostname)))
        if not parts.path:
            raise URLPathError( _("Bad URL path: {0}".format(parts.path)))
        return True
       

    def _blankForm(self):
        for key, widget in self._input.items():
            widget.set('')
        self._confirm.set('')

    def isEmpty(self, data):
         return not bool(data) or (data['url'] == '') or (data['username'] == '') or (data['password'] == '')

    # response to publishing_details_req
    def detailsResp(self, data):
        if data:
            for key,value in data.items():
                if value is not None:
                    self._input[key].set(value)
            
    # When pressing the Save button
    def onSaveButton(self):
        '''When pressing the Save Button'''
        data = { key: widget.get() for key, widget in self._input.items()}
        
        if self.isEmpty(data):
            message = _("Empty fields")
            tk.messagebox.showerror(message=message, title=_("Preferences"), parent=self)
            return
        try:
            self._checkURL()
        except ValueError as e:
            tk.messagebox.showerror(message=str(e), title=_("Preferences"), parent=self)
            return

        if not self._checkPassword():
            message = _("Passwords don't match")
            tk.messagebox.showerror(message=message, title=_("Preferences"), parent=self)
            return
        
        self._control['save'].configure(state='disabled')
        pub.sendMessage('publishing_save_req', data=data)
       
    # response to publishing_save_req
    def saveOkResp(self):
        self._control['save'].configure(state='enabled')


    # When pressing the Clear button
    def onClearButton(self):
        data = { key: widget.get() for key,widget in self._input.items()}
        if not self.isEmpty(data):
            self._control['clear'].configure(state='disabled')
            pub.sendMessage('publishing_delete_req', data=data)

    # response to publishing_delete_req
    def deleteOkResponse(self, count):
        self._control['clear'].configure(state='enabled')
        self._blankForm()

    # response to publishing_delete_req
    def deleteErrorResponse(self, count):
        message = _("I dont't know what to say.")
        tk.messagebox.showwarning(message=message, title=_("Preferences"), parent=self.master)
        self._control['clear'].configure(state='enabled')

