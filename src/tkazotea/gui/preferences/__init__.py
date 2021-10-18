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

import gettext
import tkinter as tk
from   tkinter import ttk

# -------------------
# Third party imports
# -------------------

# ---------------
# Twisted imports
# ---------------

from twisted.logger import Logger

# -------------
# local imports
# -------------

from tkazotea.gui.preferences.observer import ObserverFrame
from tkazotea.gui.preferences.location import LocationFrame
from tkazotea.gui.preferences.camera import CameraFrame
from tkazotea.gui.preferences.roi import ROIFrame
from tkazotea.gui.preferences.miscelanea import MiscelaneaFrame
from tkazotea.gui.preferences.publishing import PublishingFrame


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

class Preferences(tk.Toplevel):

    def __init__(self, owner, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._owner = owner
        self.build()
        self.grab_set()

    def start(self):
        self.observerFrame.start()
        self.locationFrame.start()
        self.cameraFrame.start()
        self.roiFrame.start()
        self.miscelaneaFrame.start()
        self.publishingFrame.start()

    def close(self):
        self._owner.preferences = None
        self.destroy()

    def build(self):
        self.title(_("Preferences"))
        self.protocol("WM_DELETE_WINDOW", self.close)
        notebook = ttk.Notebook(self)
        notebook.pack(fill='both', expand=True)        

        cam_frame = CameraFrame(
            notebook,
            label= _("Default camera"),
            initial_event="camera_list_req",
            detail_event="camera_details_req",
            default_event="camera_set_default_req",
            save_event="camera_save_req",
            delete_event="camera_delete_req",
            purge_event=None,
        )
        cam_frame.pack(fill='both', expand=True)
        notebook.add(cam_frame, text=_("Camera"))
        obs_frame = ObserverFrame(
            notebook,
            label= _("Default observer"),
            initial_event="observer_list_req",
            detail_event="observer_details_req",
            default_event="observer_set_default_req",
            save_event="observer_save_req",
            delete_event="observer_delete_req",
            purge_event=None,
        )
        obs_frame.pack(fill='both', expand=True)
        notebook.add(obs_frame, text=_("Observer"))

        loc_frame = LocationFrame(
            notebook,
            label= _("Default location"),
            initial_event="location_list_req",
            detail_event="location_details_req",
            default_event="location_set_default_req",
            save_event="location_save_req",
            delete_event="location_set_delete_req",
            purge_event=None,
        )
        loc_frame.pack(fill='both', expand=True)
        notebook.add(loc_frame, text=_("Location"))
        
        # obs_frame = ObserverFrame(notebook)
        # obs_frame.pack(fill='both', expand=True)
        # notebook.add(obs_frame, text=_("Observer"))
        
        # roi_frame = ROIFrame(notebook)
        # roi_frame.pack(fill='both', expand=True)
        # notebook.add(roi_frame, text=_("ROI"))
        
        roi_frame = ROIFrame(
            notebook,
            label= _("Default Region of Interest"),
            initial_event="roi_list_req",
            detail_event="roi_details_req",
            default_event="roi_set_default_req",
            save_event="roi_save_req",
            delete_event="roi_delete_req",
            purge_event=None,
        )
        roi_frame.pack(fill='both', expand=True)
        notebook.add(roi_frame, text=_("ROI"))

        publish_frame = PublishingFrame(notebook)
        publish_frame.pack(fill='both', expand=True)
        notebook.add(publish_frame, text=_("Publishing"))
        
        misc_frame = MiscelaneaFrame(notebook)
        misc_frame.pack(fill='both', expand=True)
        notebook.add(misc_frame, text=_("Miscelanea"))

        self.notebook        = notebook
        self.observerFrame   = obs_frame
        self.locationFrame   = loc_frame
        self.cameraFrame     = cam_frame
        self.roiFrame        = roi_frame
        self.publishingFrame = publish_frame
        self.miscelaneaFrame = misc_frame
