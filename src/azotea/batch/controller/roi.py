# ----------------------------------------------------------------------
# Copyright (c) 2020
#
# See the LICENSE file for details
# see the AUTHORS file for authors
# ----------------------------------------------------------------------

#--------------------
# System wide imports
# -------------------

# ---------------
# Twisted imports
# ---------------

from twisted.logger   import Logger
from twisted.internet.defer import inlineCallbacks

# -------------------
# Third party imports
# -------------------

#--------------
# local imports
# -------------

from azotea.logger  import setLogLevel
from azotea.batch.controller import NAMESPACE, log

# ----------------
# Module constants
# ----------------

# -----------------------
# Module global variables
# -----------------------

# ------------------------
# Module Utility Functions
# ------------------------


# --------------
# Module Classes
# --------------


class ROIController:

    def __init__(self, model, config):
        self.model = model
        self.config = config
        self.default_id = None
        self.default_details = None
        setLogLevel(namespace=NAMESPACE, levelStr='info')

    # --------------
    # Helper methods
    # --------------

    @inlineCallbacks
    def getDefault(self):
        if not self.default_id:
            # loads defaults
            info = yield self.config.load('ROI','roi_id')
            self.default_id = info['roi_id']
            if self.default_id:
                self.default_details = yield self.model.loadById(info)
        return((self.default_id,  self.default_details))
