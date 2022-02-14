# ----------------------------------------------------------------------
# Copyright (c) 2020
#
# See the LICENSE file for details
# see the AUTHORS file for authors
# ----------------------------------------------------------------------

#--------------------
# System wide imports
# -------------------

import sqlite3
import datetime

# ---------------
# Twisted imports
# ---------------

from twisted.logger import Logger
from twisted.enterprise import adbapi

#--------------
# local imports
# -------------

from azotea.logger import setLogLevel
from azotea.dbase.tables import Table, VersionedTable

# ----------------
# Module constants
# ----------------

class ROITable(Table):

    def lookupByComment(self, filter_dict):
        '''Lookup roi id by given comment'''
        def _lookupByComment(txn, filter_dict):
            model  = filter_dict['model']
            width  = filter_dict['width']
            height = filter_dict['height']
            filter_dict['comment'] = f'ROI for {model}%, centered at P=(%), width={width}, height={height}'
            sql = '''
                SELECT roi_id
                FROM roi_t
                WHERE comment LIKE :comment
            '''
            txn.execute(sql, filter_dict)
            result = txn.fetchone()
            if result:
                result = dict(zip((self._id_column,), result))
            return result
        return self._pool.runInteraction(_lookupByComment, filter_dict)
