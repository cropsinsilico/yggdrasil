#!/bin/bash

flake8 cis_interface

# IPC Comms
export CIS_DEFAULT_COMM="IPCComm"
source activate py27
nosetests -svx --nologcapture cis_interface
source activate py34
nosetests -svx --nologcapture cis_interface
source activate py35
nosetests -svx --nologcapture cis_interface
source activate py36
nosetests -svx --nologcapture cis_interface


# ZMQ Comms
export CIS_DEFAULT_COMM="ZMQComm"
source activate py27
nosetests -svx --nologcapture cis_interface
source activate py34
nosetests -svx --nologcapture cis_interface
source activate py35
nosetests -svx --nologcapture cis_interface
source activate py36
nosetests -svx --nologcapture cis_interface


unset CIS_DEFAULT_COMM
