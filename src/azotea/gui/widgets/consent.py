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

# -------------------
# Third party imports
# -------------------

from pubsub import pub
import PIL

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
# Application Class
# -----------------

class ConsentDialog(tk.Toplevel):

    def __init__(self, title, text_path, logo_path, accept_event, reject_event, reject_code, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._title = title
        self._text_path = text_path
        self._logo_path = logo_path
        self._accept_event = accept_event
        self._reject_event = reject_event
        self._reject_code = reject_code
        self.build()
        self.protocol('WM_DELETE_WINDOW', self.onRejectButton)
        self.attributes('-topmost', True)
        self.grab_set()

        
    def build(self):
        self.title(self._title)
        # TOP superframe
        top_frame = ttk.LabelFrame(self, borderwidth=2, relief=tk.GROOVE, text=_('PLEASE, READ THIS FIRST !'))
        top_frame.pack(side=tk.TOP, expand=True, fill=tk.X, padx=5, pady=5)
        # Bottom frame
        bottom_frame = ttk.Frame(self,  borderwidth=2, relief=tk.GROOVE)
        bottom_frame.pack(side=tk.BOTTOM, expand=True, fill=tk.X, padx=5, pady=5)
        # Lower Buttons
        button = ttk.Button(bottom_frame, text=_("Accept"), command=self.onAcceptButton)
        button.pack(side=tk.LEFT, padx=10, pady=5)
        button = ttk.Button(bottom_frame, text=_("Reject"), command=self.onRejectButton)
        button.pack(side=tk.RIGHT, padx=10, pady=5)
        # Text & scrollbars widgets
        text = tk.Text(top_frame, height=18, width=65)

        img = PIL.ImageTk.PhotoImage(PIL.Image.open(self._logo_path))
        icon = ttk.Label(self, image = img)
        icon.photo = img

        text.window_create(tk.END,window = icon)

        text.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=10, pady=10)
        vsb = ttk.Scrollbar(top_frame, orient=tk.VERTICAL, command=text.yview)
        vsb.pack(side=tk.RIGHT,  fill=tk.Y)
        text.config(yscrollcommand=vsb.set)
        text.insert(tk.END, self.loadText())
        text.config(state=tk.DISABLED)
        

    # Buttons callbacks
    def onRejectButton(self):
        pub.sendMessage(self._reject_event, exit_code = self._reject_code)
        self.destroy()

     # Buttons callbacks
    def onAcceptButton(self):
        pub.sendMessage(self._accept_event)
        self.destroy()


    def loadText(self):
        with open(self._text_path) as fd:
            lines = fd.readlines()
        return ' '.join(lines)

    def loadIcon(self, parent, path):
        img = PIL.ImageTk.PhotoImage(PIL.Image.open(path))
        icon = ttk.Label(parent, image = img)
        icon.photo = img
        return icon

