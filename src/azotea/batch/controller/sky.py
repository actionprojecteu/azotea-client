# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------
# Copyright (c) 2020
#
# See the LICENSE file for details
# see the AUTHORS file for authors
# ----------------------------------------------------------------------

#--------------------
# System wide imports
# -------------------

import os.path
import csv

# ---------------
# Twisted imports
# ---------------

from twisted.logger   import Logger
from twisted.internet.defer import inlineCallbacks
from twisted.internet.threads import deferToThread

# -------------------
# Third party imports
# -------------------

from pubsub import pub

#--------------
# local imports
# -------------

from azotea.logger  import setLogLevel
from azotea.utils.roi import Rect
from azotea.utils.sky import CSV_COLUMNS, postprocess, widget_datetime, processImage
from azotea import FITS_HEADER_TYPE, EXIF_HEADER_TYPE
from azotea import DATE_SELECTION_ALL, DATE_SELECTION_DATE_RANGE, DATE_SELECTION_LATEST_NIGHT, DATE_SELECTION_LATEST_MONTH
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

class SkyBackgroundController:

    NAME = NAMESPACE
    
    def __init__(self, parent, config, model, export_type, csv_dir, pub_flag):
        self.parent = parent
        self.model  = model
        self.sky    = model.sky
        self.image  = model.image
        self.roi    = model.roi 
        self.pub_flag = pub_flag
        self.config = config
        self.export_type = export_type
        self.csv_dir    = csv_dir
        self.observerCtrl = None
        self.roiCtrl      = None
        setLogLevel(namespace=NAMESPACE, levelStr='info')
        self.start()
           
    def start(self):
        log.info('starting Sky Background Controller')
        pub.subscribe(self.onStatsReq,  'sky_brightness_stats_req')
        pub.subscribe(self.onExportReq, 'sky_brightness_csv_req')

    

    # -----------------------
    # Subscriptions from View
    # -----------------------

    @inlineCallbacks
    def onStatsReq(self):
        result = yield self.doCheckDefaults()
        if result:
            yield self.doStats()
        else:
            pub.sendMessage('file_quit')


    @inlineCallbacks
    def onExportReq(self, date):
        result = yield self.doCheckDefaultsExport()
        if result:
            yield self.doExport(date)
        else:
            pub.sendMessage('file_quit')


    # -------
    # Helpers
    # -------

    def triggerExport(self):
        log.info("")
        data = dict()
        export_type = self.export_type
        if export_type == 'day':
            data['date_selection'] = DATE_SELECTION_LATEST_NIGHT
        elif export_type == 'month':
            data['date_selection'] = DATE_SELECTION_LATEST_MONTH
        else: 
            data['date_selection'] = DATE_SELECTION_ALL
        pub.sendMessage("sky_brightness_csv_req", date=data)


    @inlineCallbacks
    def doCheckDefaults(self):
        result = True
        errors = list()
        log.debug('doCheckDefaults()')
        default_roi_id, tmp = yield self.roiCtrl.getDefault()
        if default_roi_id:
            self.roi_id = int(default_roi_id)
        else:
            self.roi_id = None
            errors.append( _("- No default ROI selected.") )
        if errors:
            error_list = '\n'.join(errors)
            message = _("These things are missing:\n{0}").format(error_list)
            log.error("Sky Background Processor: {m}", m=message)
            result = False
        return(result)


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
            log.error("Sky Background Processor: {m}", m=message)
            result = False
        return(result)



    @inlineCallbacks
    def doExport(self, date):
        filter_dict = {'observer_id': self.observer_id}
        date_selection = date['date_selection']
        if date_selection == DATE_SELECTION_ALL:
            filename = f'{self.observer_name}-all.csv'
            contents = yield self.sky.exportAll(filter_dict)
        elif date_selection == DATE_SELECTION_LATEST_NIGHT:
            year, month, day = yield self.sky.getLatestNight(filter_dict)
            filename = f'{self.observer_name}-{year}{month}{day:02d}.csv'
            contents = yield self.sky.exportLatestNight(filter_dict)
        elif date_selection == DATE_SELECTION_LATEST_MONTH:
            year, month, day = yield self.sky.getLatestMonth(filter_dict)
            filename = f'{self.observer_name}-{year}{month}{day:02d}.csv'
            contents = yield self.sky.exportLatestMonth(filter_dict)
        elif date_selection == DATE_SELECTION_DATE_RANGE:
            filter_dict['start_date_id'] = int(date['start_date'])
            filter_dict['end_date_id']   = int(date['end_date'])
            filename = f"{self.observer_name}-{date['start_date']}-{date['end_date']}.csv"
            contents = yield self.sky.exportDateRange(filter_dict)
        else:
            log.error("ESTO NO DEBERIA DARSE")
        os.makedirs(self.csv_dir, exist_ok=True)
        path = os.path.join(self.csv_dir, filename)
        with open(path,'w') as fd:
            writer = csv.writer(fd, delimiter=';')
            writer.writerow(CSV_COLUMNS)
            for row in contents:
                row = map(postprocess, enumerate(row))
                writer.writerow(row)
        log.info("Export {what} complete: {path}", what=self.export_type, path=path)
        if self.pub_flag:
            pub.sendMessage('publishing_publish_req')
        else:
            pub.sendMessage('file_quit')



    @inlineCallbacks
    def doStats(self):
        # Default settings extracted by doCheckDefaults()
        conditions = {
            'roi_id'     : self.roi_id,
        }
        roi_dict = yield self.roi.loadById({'roi_id': self.roi_id})
        rect = Rect.from_dict(roi_dict)
        image_id_list = yield self.sky.pending(conditions)
        N_stats = len(image_id_list)
        for i, (image_id,) in enumerate(image_id_list):
            name, directory, exptime, cfa_pattern, camera_id, date_id, time_id, observer_id, location_id = yield self.image.getInitialMetadata({'image_id':image_id})
            w_date, w_time = widget_datetime(date_id, time_id) 
            row = {
                'name'       : name,
                'image_id'   : image_id,
                'observer_id': observer_id,
                'location_id': location_id,
                'roi_id'     : self.roi_id,
                'camera_id'  : camera_id,
                'date_id'    : date_id,
                'time_id'    : time_id,
                'widget_date': w_date,  # for display purposes only
                'widget_time': w_time,  # for display purposes only
                'exptime'    : exptime, # for display purposes only
            }
            try:
                yield deferToThread(processImage, name, directory, rect, cfa_pattern, row)
            except Exception as e:
                log.failure('{e}', e=e)
                log.error("Sky Background Processor: {name} [{p}%]", name=row['name'], p=(100*i//N_stats))
                return(None)
            else:
                log.info("Sky Background Processor: {name} [{p}%]", name=row['name'], p=(100*i//N_stats))
                yield self.sky.save(row)
        if N_stats:
            log.info("Sky Background Processor: {n}/{d} images processed", n=i+1, d=N_stats)
        else:
            log.info("Sky Background Processor: No images to process")
        if self.export_type and self.csv_dir:
            log.info("Sky Background Processor: Generating CSV file")
            self.triggerExport()
        elif self.pub_flag:
            pub.sendMessage('publishing_publish_req')
        else:
            pub.sendMessage('file_quit')