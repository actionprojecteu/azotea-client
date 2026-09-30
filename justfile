anew:
    #!/usr/bin/env bash
    set -exuo pipefail
    rm -f azotea.db azotea.log

env:
    uv venv --python 3.12
    mkdir csv log

install:
    uv pip install "setuptools<82"
    uv pip install -e .

setup:
    #!/usr/bin/env bash
    set -exuo pipefail
    AZOTEA_HOME=$(pwd)                                   
    DBASE=${AZOTEA_HOME}/azotea.db                              
    IMAGES=${AZOTEA_HOME}/images
    LOG=${AZOTEA_HOME}/log/azotea.log
    CSV_DIR=${AZOTEA_HOME}/csv
    uv run azotool --console  --log-file ${LOG} --dbase ${DBASE} consent view  --agree


export-all:
    #!/usr/bin/env bash
    set -exuo pipefail
    AZOTEA_HOME=$(pwd)                                   
    DBASE=${AZOTEA_HOME}/azotea.db                              
    LOG=${AZOTEA_HOME}/log/azotea.log
    CSV_DIR=${AZOTEA_HOME}/csv
    uv run azotool --console --log-file ${LOG} --dbase ${DBASE} sky export --all --csv-dir ${CSV_DIR}
   
