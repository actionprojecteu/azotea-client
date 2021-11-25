# ----------------------------------------------------------------------
# Copyright (c) 2020
#
# See the LICENSE file for details
# see the AUTHORS file for authors
# ----------------------------------------------------------------------

#--------------------
# System wide imports
# -------------------

import os
import csv
import math
import random 

# ---------------
# Twisted imports
# ---------------

from twisted.logger   import Logger
from twisted.internet.defer import inlineCallbacks
from twisted.internet.threads import deferToThread

# -------------------
# Third party imports
# -------------------

import tabulate
from pubsub import pub

#--------------
# local imports
# -------------

from azotea import DATE_SELECTION_ALL, DATE_SELECTION_UNPUBLISHED
from azotea import DATE_SELECTION_DATE_RANGE, DATE_SELECTION_LATEST_NIGHT, DATE_SELECTION_LATEST_MONTH
from azotea.logger  import setLogLevel
from azotool.cli   import NAMESPACE, log
from azotea.utils.sky import CSV_COLUMNS, postprocess

# ----------------
# Module constants
# ----------------

EXPORT_INTERNAL_DATE_FMT = '%Y%m%d'

# -----------------------
# Module global variables
# -----------------------

# ------------------------
# Module Utility Functions
# ------------------------

# --------------
# Module Classes
# --------------

class ImageController:

    def __init__(self, model, config):
        self.model  = model
        self.image    = model.image
        self.config = config
        setLogLevel(namespace=NAMESPACE, levelStr='info')
        pub.subscribe(self.onSummaryReq,  'image_summary_req')


    @inlineCallbacks
    def onSummaryReq(self, options):
        try:
            result = yield self.image.summaryStatistics()
            result=list(map(lambda t: (', '.join((t[0],t[1])), t[2], bool(t[3]), t[4]), result))
            headers=("Observer", "Type", "Corrupt?", "# Images")
            log.info("\n{t}", t=tabulate.tabulate(result, headers=headers, tablefmt='grid'))
        except Exception as e:
            log.failure('{e}',e=e)
            pub.sendMessage('quit', exit_code = 1)
        else:
            pub.sendMessage('quit')

