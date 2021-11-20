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
import datetime
import gettext
import tkinter as tk
from   tkinter import ttk
import tkinter.filedialog

# -------------------
# Third party imports
# -------------------

# ---------------
# Twisted imports
# ---------------

from twisted.logger import Logger
from tkcalendar import Calendar, DateEntry

# -------------
# local imports
# -------------

from azotea import __version__
from azotea import DATE_SELECTION_ALL, DATE_SELECTION_DATE_RANGE, DATE_SELECTION_LATEST_NIGHT, DATE_SELECTION_LATEST_MONTH

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

# -----------------
# Application Class
# -----------------

class DateFilterDialog(tk.Toplevel):

    def __init__(self, parent, command, title=_("Date Filter"), date_fmt='%Y%m%d', **kwargs):
        super().__init__(parent,**kwargs)
        self._input   = {}
        self._control = {}
        self._command = command
        self._date_fmt = date_fmt
        self._title = title
        self.build()
        self.grab_set()
        self.onRadioButton()
        
        
    def build(self, ncols=3):
        self.title(self._title)

        # TOP superframe
        top_frame = ttk.Frame(self,  borderwidth=2, relief=tk.GROOVE)
        top_frame.pack(side=tk.TOP, expand=True, fill=tk.X, padx=5, pady=5)
        
        # Bottom frame
        bottom_frame = ttk.Frame(self,  borderwidth=2, relief=tk.GROOVE)
        bottom_frame.pack(side=tk.BOTTOM, expand=True, fill=tk.X, padx=5, pady=5)
        # Lower Button
        button1 = ttk.Button(bottom_frame, text=_("Ok"), command=self.onOkButton)
        button1.pack(side=tk.LEFT, padx=5, pady=5)

        button2 = ttk.Button(bottom_frame, text=_("Cancel"), command=self.onCancelButton)
        button2.pack(side=tk.RIGHT, padx=5, pady=5)

        # Rabiobuttons selection
        subframe1 = ttk.LabelFrame(top_frame,text=_("Date filter selection"))
        subframe1.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self._method  = dateVar = tk.StringVar()
        button1 = ttk.Radiobutton(subframe1, text=_("All"), command=self.onRadioButton, variable=dateVar, value=DATE_SELECTION_ALL)
        button1.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self._control['all_dates'] = button1
        button2 = ttk.Radiobutton(subframe1, text=_("Latest night"), command=self.onRadioButton, variable=dateVar, value=DATE_SELECTION_LATEST_NIGHT)
        button2.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self._control['latest_night'] = button2
        button3 = ttk.Radiobutton(subframe1, text=_("Latest month"), command=self.onRadioButton, variable=dateVar, value=DATE_SELECTION_LATEST_MONTH)
        button3.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self._control['latest_month'] = button3
        button4 = ttk.Radiobutton(subframe1, text=_("Date range"), command=self.onRadioButton, variable=dateVar, value=DATE_SELECTION_DATE_RANGE)
        button4.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self._control['date_range'] = button4
        dateVar.set(DATE_SELECTION_ALL)

        # Date range selection
        subframe2 = ttk.LabelFrame(top_frame,text=_("Date range selection"))
        subframe2.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
        label1 = ttk.Label(subframe2, text=_("Start date"))
        label1.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
        cal1 = DateEntry(subframe2, width=12, date_pattern='y-mm-dd')
        cal1.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
        label2 = ttk.Label(subframe2, text=_("End date"))
        label2.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
        cal2 = DateEntry(subframe2, width=12, date_pattern="y-mm-dd")
        cal2.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self._control['start_date'] = cal1
        self._control['end_date'] = cal2


    # Buttons callbacks
    def onRadioButton(self):
        state = self._method.get()
        if state == 'Date range':
            for key in ('start_date','end_date'):
                self._control[key].configure(state='enabled')
        else:
            for key in ('start_date','end_date'):
                self._control[key].configure(state='disabled')
        

    def onCancelButton(self):
       self.destroy()

    def onOkButton(self):
        data = {}
        method = self._method.get()
        data['date_selection'] = method
        if method == 'Date range':
            data['start_date'] =  self._control['start_date'].get_date().strftime(self._date_fmt)
            data['end_date']   =  self._control['end_date'].get_date().strftime(self._date_fmt)
        log.info("DATA {data}",data=data)
        if self._command:
            self._command(data)
        self.destroy()

    

