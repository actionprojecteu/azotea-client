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
import sys
import datetime

# ---------------
# Twisted imports
# ---------------

#--------------
# local imports
# -------------

from azotea import SQL_SCHEMA, SQL_INITIAL_DATA_DIR, SQL_UPDATES_DATA_DIR
from azotea.consent import CONSENT_TXT
from azotea.utils.database import create_database, create_schema

# ----------------
# Module constants
# ----------------

SQL_TEST_STRING = "SELECT COUNT(*) FROM image_t"

# --------------
# Module Classes 
# --------------


# -----------------------
# Module global variables
# -----------------------


# ------------------------
# Module Utility Functions
# ------------------------

def get_database_connection(path):
    connection, new_database = create_database(path)
    create_schema(connection, SQL_SCHEMA, SQL_INITIAL_DATA_DIR, SQL_UPDATES_DATA_DIR, SQL_TEST_STRING)
    connection.commit()
    return connection

def check_agreement(connection):
    cursor = connection.cursor()
    cursor.execute("SELECT value from config_t WHERE section = 'gdpr' AND property = 'agree'")
    value = cursor.fetchone()
    if value:
        result = value[0] == 'Yes'
    else:
        result = False
    return result

def save_agreement(connection):
    cursor = connection.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO config_t(section, property, value)
        VALUES('gdpr', 'agree', 'Yes')
        ''')
    row = {
        'tstamp': datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    }
    cursor.execute('''
        INSERT OR REPLACE INTO config_t(section, property, value)
        VALUES('gdpr', 'tstamp', :tstamp)
        ''', row)
    connection.commit()

def view():
    with open(CONSENT_TXT) as fd:
        lines = fd.readlines()
    text = ''.join(lines)
    print(text)
    try:
        key = input()
    except KeyboardInterrupt:
        return False
    else:
        return key == 'y'