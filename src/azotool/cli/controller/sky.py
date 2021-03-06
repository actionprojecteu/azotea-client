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
from azotea.utils.sky import CSV_COLUMNS, csv_postprocess

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

class SkyController:

    def __init__(self, model, config):
        self.model  = model
        self.sky    = model.sky
        self.config = config
        setLogLevel(namespace=NAMESPACE, levelStr='info')
        pub.subscribe(self.onExportReq,  'sky_export_req')
        pub.subscribe(self.onSummaryReq, 'sky_summary_req')


    @inlineCallbacks
    def onSummaryReq(self, options):
        try:
            result = yield self.sky.summaryStatistics()
            result=list(map(lambda t: (', '.join((t[0],t[1])), t[2], t[3], t[4], bool(t[5]), t[6]), result))
            headers=("Observer", "ROI", "Width", "Height", "Published?", "# Processed images", )
            log.info("\n{t}", t=tabulate.tabulate(result, headers=headers, tablefmt='grid'))
            result = yield self.sky.rangeSummary()
            result=list(map(lambda t: (', '.join((t[0],t[1])), t[2], t[3], t[4]), result))
            headers=("Observer", "From", "To", "# Processed images", )
            log.info("\n{t}", t=tabulate.tabulate(result, headers=headers, tablefmt='grid'))
        except Exception as e:
            log.failure('{e}',e=e)
            pub.sendMessage('quit', exit_code = 1)
        else:
            pub.sendMessage('quit')



    @inlineCallbacks
    def onExportReq(self, options):
        try:
            self.csv_dir = options.csv_dir
            result = yield self.doCheckDefaultsExport()
            if not result:
                return(None)
            date = dict()
            if options.all:
                date['date_selection'] = DATE_SELECTION_ALL
            elif options.unpublished:
                date['date_selection'] = DATE_SELECTION_UNPUBLISHED
            elif options.latest_night:
                date['date_selection'] = DATE_SELECTION_LATEST_NIGHT
            elif options.latest_month:
                date['date_selection'] = DATE_SELECTION_LATEST_MONTH
            elif options.range:
                if not options.from_date or not options.to_date:
                    raise ValueError("Missing --from-date or --to-date")
                date['date_selection'] = DATE_SELECTION_DATE_RANGE
                date['start_date'] = options.from_date.strftime(EXPORT_INTERNAL_DATE_FMT)
                date['end_date']   = options.to_date.strftime(EXPORT_INTERNAL_DATE_FMT)
            else:
                raise ValueError("This should never happen")
            yield self.doExport(date)
        except Exception as e:
            log.failure('{e}',e=e)
            pub.sendMessage('quit', exit_code = 1)
        else:
            pub.sendMessage('quit')


    def _exportCSV(self, path, contents):
        '''This can be heavy I/O bound for large datasets'''
        with open(path,'w') as fd:
            writer = csv.writer(fd, delimiter=';')
            writer.writerow(CSV_COLUMNS)
            for row in contents:
                row = map(csv_postprocess, enumerate(row))
                writer.writerow(row)

    @inlineCallbacks
    def doCheckDefaultsExport(self):
        result = True
        errors = list()
        default_roi_id, tmp = yield self.roiCtrl.getDefault()
        if default_roi_id:
            self.roi_id = int(default_roi_id)
        else:
            self.roi_id = None
            errors.append("- No default ROI selected.")
        default_observer_id, default_observer_details = yield self.observerCtrl.getDefault()
        if default_observer_id:
            self.observer_id = int(default_observer_id)
            self.observer_name = default_observer_details['surname'].replace(' ', '_')
        else:
            self.observer_id = None
            errors.append("- No default observer selected.")
        if errors:
            error_list = '\n'.join(errors)
            message = _("These things are missing:\n{0}").format(error_list)
            log.error("Azotea tool: {m}", m=message)
            result = False
        return(result)



    @inlineCallbacks
    def doExport(self, date):
        filter_dict = {'observer_id': self.observer_id}
        date_selection = date['date_selection']
        if date_selection == DATE_SELECTION_ALL:
            filename = f'{self.observer_name}-all.csv'
            contents = yield self.sky.exportAll(filter_dict)
        elif date_selection == DATE_SELECTION_UNPUBLISHED:
            filename = f'{self.observer_name}-unpublished.csv'
            contents = yield self.sky.exportUnpublished(filter_dict)
        elif date_selection == DATE_SELECTION_LATEST_NIGHT:
            year, month, day = yield self.sky.getLatestNight(filter_dict)
            filename = f'{self.observer_name}-{year}{month}{day:02d}.csv'
            contents = yield self.sky.exportLatestNight(filter_dict)
        elif date_selection == DATE_SELECTION_LATEST_MONTH:
            year, month, day = yield self.sky.getLatestMonth(filter_dict)
            filename = f'{self.observer_name}-{year}{month}{day:02d}.csv'
            contents = yield self.sky.exportLatestMonth(filter_dict)
        else:
            filter_dict['start_date_id'] = int(date['start_date'])
            filter_dict['end_date_id']   = int(date['end_date'])
            filename = f"{self.observer_name}-{date['start_date']}-{date['end_date']}.csv"
            contents = yield self.sky.exportDateRange(filter_dict)
        os.makedirs(self.csv_dir, exist_ok=True)
        path = os.path.join(self.csv_dir, filename)
        yield deferToThread(self._exportCSV, path, contents)
        log.info("Export {what} complete: {path}", what=date_selection, path=path)

