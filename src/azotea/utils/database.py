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
import os.path
import glob
import sqlite3

# -------------------
# Third party imports
# -------------------

#--------------
# local imports
# -------------


# ----------------
# Module constants
# ----------------

# -----------------------
# Module global variables
# -----------------------

# ------------------------
# Module Utility Functions
# ------------------------

def create_database(dbase_path):
    '''Creates a Database file if not exists and returns a connection'''
    new_database = False
    output_dir = os.path.dirname(dbase_path)
    if not output_dir:
        output_dir = os.getcwd()
    os.makedirs(output_dir, exist_ok=True)
    if not os.path.exists(dbase_path):
        with open(dbase_path, 'w') as f:
            pass
        new_database = True
    return sqlite3.connect(dbase_path), new_database


def create_schema(connection, schema_path, initial_data_dir_path, updates_data_dir, query):
    created = True
    cursor = connection.cursor()
    try:
        cursor.execute(query)
    except Exception:
        created = False
    if not created:
        with open(schema_path) as f: 
            lines = f.readlines() 
        script = ''.join(lines)
        connection.executescript(script)
        #log.info("Created data model from {0}".format(os.path.basename(schema_path)))
        file_list = glob.glob(os.path.join(initial_data_dir_path, '*.sql'))
        for sql_file in file_list:
            #log.info("Populating data model from {0}".format(os.path.basename(sql_file)))
            with open(sql_file) as f: 
                lines = f.readlines() 
            script = ''.join(lines)
            connection.executescript(script)
    else:
        file_list = glob.glob(os.path.join(updates_data_dir, '*.sql'))
        for sql_file in file_list:
            #log.info("Applying updates to data model from {0}".format(os.path.basename(sql_file)))
            with open(sql_file) as f: 
                lines = f.readlines() 
            script = ''.join(lines)
            connection.executescript(script)
    connection.commit()
    return not created, file_list