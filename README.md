# AZOTEA Client

Sky background image reduction tool for the [AZOTEA project](https://guaix.ucm.es/azoteaproject) sky background image reduction tool.
Development of this software has been possible through [ACTION - Participatory science toolkit against pollution](https://actionproject.eu/), Grant 824603.

**Highlights**

* Rich client GUI interactive mode.
* Non interactive command line mode for automated data adquisition, reducition and publishing.

# Installation

This is a Python tool that runs on *only* in Python 3 (tested on Python 3.6) 
It is *highly recommended* to be installed and run in its *own virtual environment*.
This can be easily done in Python 3 with a few lines. See the script below

```bash
#!/bin/bash
python3 -m venv ${HOME}/azotea
mkdir -p ${HOME}/azotea/images
mkdir -p ${HOME}/azotea/log
. ${HOME}/azotea/bin/activate
pip install git+https://github.com/actionprojecteu/azotea-client.git@main
```

* The first line creates a Python virtual environment under `${HOME}/azotea`.
* The second and third lines create additional subdirectiores under this virtual environment for log files and camera images.
* The third line activates the virtual environment (**please note the starting dot**) so that all needed python packages are installed there and not system wide.
* The fourth line install the software from [its GitHub repository](https://github.com/actionprojecteu/azotea-client)

```

There is an error showing `Building wheel for azotea-client (setup.py) ... error` but it seems ok.
Verify it by executing

```bash
azotool --version
````

# Configuration

The software requires the same configuration whether it is run either in GUI or batch mode:
* Enter observer's data.
* Enter location's data.
* Enter cameras's data.
* Enter Region of Interest data
* Enter miscelaneous data (default optics configuration, publishing credentials)

We'll walk through it using command line tools available for the batch mode, using a ficticious but prototypical example.

Juan Gómez Pérez is a Spanish amateur astronomer, member of the *Agrupación Astronómica de Alcafrán* (AA-ACFN), wishing to join the AZOTEA project using his *Cannon EOS 550D* reflex camera. As he uses it for other purposes, the time set in the camera is the local time, not UTC. His observing site is within the small population of Alcafrán (40.4966031 N, 2.7335649 W). As he has an old 180mm f/3.5 objective lens, the RAW camera files don't automatically capture this information. He will be measuring sky background in the central rectangular field of view of 500x400 pixels.

The following series of commands must be issued. This can be edited in a file and run together in a script. For simplicity's sake
error codes are not checked.

```bash
export PATH=${HOME}/azotea/bin:/usr/local/bin:/usr/bin:/bin
export VIRTUAL_ENV=${HOME}/azotea
DBASE=${HOME}/azotea/azotea.db

azotool --console --dbase ${DBASE} consent view

azotool --console --dbase ${DBASE} observer create --default --name Juan --surname Gómez Pérez \
        --affiliation Agrupación Astronómica de Alcafrán --acronym AA-ACFN

azotool --console --dbase ${DBASE} location create --default --site-name Alcafrán --location Alcafrán \
        --longitude -2.7335649 --latitude 40.4966031 --utc-offset 1

azotool --console --dbase ${DBASE} camera create --default \
        --from-image ${HOME}/azotea/images/2021-11-22/IMG_0164.CR2

azotool --console --dbase ${DBASE} roi create --default --width 500 --height 400 \
        --from-image ${HOME}/azotea/images/2021-11-22/IMG_0164.CR2

azotool --console --dbase ${DBASE} miscelanea optics --focal-length 180 --f-number 3.5

azotool --console --dbase ${DBASE} miscelanea publishing --username foo --password bar
```

# Automation

## Log file & console output

It is highly recommeded to configure a log file when executing azotea in batch mode. This log file is not rotated.
For the same reason, console output is not activated by default and must be explicitely activated with `--console`
Redirecting  console `stdout` `stderr` has the same effect as specifying a log file but it is a bit more cumbersome.

## Exit codes

The command exit codes are:
* 0 => Command ended without errors
* 1 => Command ended with errors. See the console (if set) or the log file.
* 126 => User did not agree the usage conditions

PATH={{ tessdb_venv_dir }}/bin:/usr/local/bin:/usr/bin:/bin
PYTHONIOENCODING=utf-8
#PYTHONPATH={{ tessdb_venv_dir }}/lib/python/3.6/site-packages
VIRTUAL_ENV={{ tessdb_venv_dir }}


